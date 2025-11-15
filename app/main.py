"""Main FastAPI application for capa-server."""
import json
import logging
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, Analysis
from app.analyzer import analyzer

# Import badsign modules for YARA and ClamAV generation
try:
    from badsign.capa_parser import CapaParser
    from badsign.yara_generator import YaraGenerator
    from badsign.core import ClamAVSigGen
    YARA_GENERATION_AVAILABLE = True
    CLAMAV_GENERATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"badsign not available: {e}")
    YARA_GENERATION_AVAILABLE = False
    CLAMAV_GENERATION_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Automated malware capability analysis using capa",
)

# CORS middleware (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Helper Functions
# ============================================================================

def perform_analysis(analysis_id: int, file_path: Path):
    """
    Background task to perform capa analysis.

    Args:
        analysis_id: Database ID of the analysis
        file_path: Path to the uploaded file
    """
    from app.database import Session, engine
    from app.clamav_scanner import scanner
    from datetime import datetime

    db = Session(engine)
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return

        # Update status
        analysis.status = "processing"
        db.commit()

        # Step 1: ClamAV pre-scan
        logger.info(f"Analysis {analysis_id}: Starting ClamAV scan")
        clamav_result = scanner.scan_file(file_path)

        analysis.clamav_scanned = clamav_result['scanned']
        analysis.clamav_status = clamav_result['status']
        analysis.clamav_signature = clamav_result['signature']
        analysis.clamav_scan_time = clamav_result['scan_time']

        if clamav_result['status'] == 'infected':
            logger.warning(f"Analysis {analysis_id}: ClamAV detected malware: {clamav_result['signature']}")
        elif clamav_result['status'] == 'clean':
            logger.info(f"Analysis {analysis_id}: ClamAV scan clean")
        else:
            logger.warning(f"Analysis {analysis_id}: ClamAV scan error: {clamav_result.get('error')}")

        db.commit()

        # Step 2: Perform capa analysis
        try:
            logger.info(f"Analysis {analysis_id}: Starting capa analysis")
            result = analyzer.analyze_file(file_path)
            summary = analyzer.extract_summary(result)

            # Update database with results
            analysis.status = "completed"
            analysis.capa_version = summary["capa_version"]
            analysis.capabilities_count = summary["capabilities_count"]
            analysis.attack_techniques = json.dumps(summary["attack_techniques"])
            analysis.result_json = json.dumps(result)

            # Save results to file
            result_file = settings.results_dir / f"{analysis_id}.json"
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2)

            logger.info(f"Analysis {analysis_id} completed successfully")

        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {e}", exc_info=True)
            analysis.status = "failed"
            analysis.error_message = str(e)

        db.commit()

    except Exception as e:
        logger.error(f"Failed to process analysis {analysis_id}: {e}", exc_info=True)
    finally:
        db.close()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/api/info")
async def get_info():
    """Get server information."""
    try:
        analyzer.load_rules()
        rules_count = len(analyzer._rules) if analyzer._rules else 0
    except Exception as e:
        logger.error(f"Failed to load rules: {e}")
        rules_count = 0

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "capa_rules_count": rules_count,
        "max_file_size_mb": settings.max_file_size_mb,
        "yara_generation_available": YARA_GENERATION_AVAILABLE,
    }


@app.post("/api/analyze")
async def analyze_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a file for analysis.

    Args:
        file: Binary file to analyze
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Analysis metadata with ID for tracking
    """
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset

    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Generate timestamp-based filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")[:100]
    stored_filename = f"{timestamp}_{safe_filename}"
    file_path = settings.upload_dir / stored_filename

    # Save uploaded file
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Compute file hash
    file_hash = analyzer.compute_file_hash(file_path)

    # Check for duplicate
    existing = db.query(Analysis).filter(Analysis.file_hash == file_hash).first()
    if existing:
        logger.info(f"Duplicate file detected: {file_hash}")
        # Delete the duplicate upload
        file_path.unlink()
        return {
            "message": "File already analyzed",
            "analysis_id": existing.id,
            "duplicate": True,
        }

    # Create database entry
    analysis = Analysis(
        filename=file.filename,
        file_hash=file_hash,
        file_size=file_size,
        file_path=str(file_path),
        status="pending",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Start background analysis
    background_tasks.add_task(perform_analysis, analysis.id, file_path)

    logger.info(f"Started analysis {analysis.id} for {file.filename}")

    return {
        "message": "Analysis started",
        "analysis_id": analysis.id,
        "duplicate": False,
    }


@app.get("/api/analyses")
async def list_analyses(
    limit: int = 100,
    offset: int = 0,
    status: str = None,
    db: Session = Depends(get_db),
):
    """
    List all analyses.

    Args:
        limit: Maximum number of results
        offset: Offset for pagination
        status: Filter by status (optional)
        db: Database session

    Returns:
        List of analyses
    """
    query = db.query(Analysis).order_by(Analysis.created_at.desc())

    if status:
        query = query.filter(Analysis.status == status)

    total = query.count()
    analyses = query.limit(limit).offset(offset).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "analyses": [a.to_dict() for a in analyses],
    }


@app.get("/api/analyses/{analysis_id}")
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Get specific analysis with full results.

    Args:
        analysis_id: Analysis ID
        db: Database session

    Returns:
        Analysis with results
    """
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis.to_dict_with_results()


@app.get("/api/analyses/{analysis_id}/download")
async def download_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Download analysis results as JSON file.

    Args:
        analysis_id: Analysis ID
        db: Database session

    Returns:
        JSON file download
    """
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")

    result_file = settings.results_dir / f"{analysis_id}.json"

    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    return FileResponse(
        result_file,
        media_type="application/json",
        filename=f"capa-analysis-{analysis_id}.json",
    )


@app.get("/api/analyses/{analysis_id}/generate-yara")
async def generate_yara_rule(
    analysis_id: int,
    rule_name: Optional[str] = Query(None, description="Custom YARA rule name (auto-generated if not provided)"),
    min_confidence: str = Query("medium", description="Minimum confidence level: low, medium, or high"),
    min_capabilities: int = Query(2, description="Minimum capabilities required in rule condition"),
    db: Session = Depends(get_db)
):
    """
    Generate a YARA rule from capa analysis results.

    Args:
        analysis_id: Analysis ID
        rule_name: Optional custom rule name
        min_confidence: Confidence level (low/medium/high)
        min_capabilities: Minimum number of capabilities to require
        db: Database session

    Returns:
        YARA rule as downloadable .yar file
    """
    # Check if YARA generation is available
    if not YARA_GENERATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="YARA generation not available. clamav-siggen package not installed."
        )

    # Validate parameters
    if min_confidence not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="min_confidence must be 'low', 'medium', or 'high'")

    if min_capabilities < 1:
        raise HTTPException(status_code=400, detail="min_capabilities must be >= 1")

    # Get analysis from database
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {analysis.status}"
        )

    if not analysis.result_json:
        raise HTTPException(status_code=404, detail="Analysis results not available")

    try:
        # Parse capa JSON results
        logger.info(f"Generating YARA rule for analysis {analysis_id}")
        capa_data = json.loads(analysis.result_json)

        parser = CapaParser(capa_dict=capa_data)

        # Get sample info and capabilities
        sample_info = parser.get_sample_info()
        capabilities = parser.get_capabilities()

        logger.info(f"Sample: {sample_info.get('sha256', 'unknown')[:16]}...")
        logger.info(f"Format: {sample_info.get('format', 'unknown')}")
        logger.info(f"Capabilities detected: {len(capabilities)}")

        # Categorize malware
        category = parser.categorize_malware()
        logger.info(f"Detected category: {category}")

        # Generate YARA rule
        generator = YaraGenerator(parser)

        yara_rule = generator.generate_rule(
            rule_name=rule_name,
            min_capabilities=min_capabilities,
            min_confidence=min_confidence
        )

        # Save to temporary file for download
        yara_file = settings.results_dir / f"yara_{analysis_id}.yar"
        yara_file.write_text(yara_rule)

        logger.info(f"YARA rule generated successfully for analysis {analysis_id}")

        # Return as downloadable file
        return FileResponse(
            yara_file,
            media_type="text/plain",
            filename=f"capa-analysis-{analysis_id}.yar",
            headers={
                "Content-Disposition": f'attachment; filename="capa-analysis-{analysis_id}.yar"'
            }
        )

    except ValueError as e:
        logger.error(f"Failed to generate YARA rule: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating YARA rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate YARA rule: {str(e)}")


@app.get("/api/analyses/{analysis_id}/generate-clamav")
async def generate_clamav_signatures(
    analysis_id: int,
    sig_name: Optional[str] = Query(None, description="Custom signature name (auto-generated if not provided)"),
    include_strings: bool = Query(True, description="Include string-based body signatures"),
    string_count: int = Query(10, description="Number of string signatures to generate"),
    db: Session = Depends(get_db)
):
    """
    Generate ClamAV signatures from analysis results.

    Args:
        analysis_id: Analysis ID
        sig_name: Optional custom signature name
        include_strings: Whether to include string-based signatures
        string_count: Number of string signatures
        db: Database session

    Returns:
        ClamAV signatures as downloadable .ndb file
    """
    # Check if ClamAV generation is available
    if not CLAMAV_GENERATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ClamAV signature generation not available. clamav-siggen package not installed."
        )

    # Get analysis from database
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {analysis.status}"
        )

    if not analysis.result_json:
        raise HTTPException(status_code=404, detail="Analysis results not available")

    try:
        # Generate signature name if not provided
        if not sig_name:
            # Use filename without extension
            sig_name = Path(analysis.filename).stem.replace(" ", "_").replace(".", "_")
            # Sanitize
            sig_name = "".join(c for c in sig_name if c.isalnum() or c == "_")
            if not sig_name:
                sig_name = f"Malware_{analysis_id}"

        logger.info(f"Generating ClamAV signatures for analysis {analysis_id}")

        # Load the original file
        file_path = Path(analysis.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Original file not found")

        # Initialize ClamAV signature generator
        siggen = ClamAVSigGen(file_path=file_path)

        # Generate all signature types
        signatures = siggen.generate_all(
            name=sig_name,
            include_strings=include_strings,
            string_count=string_count
        )

        # Build output text file with multiple signature formats
        output_lines = []

        # Add header comment
        output_lines.append(f"# ClamAV Signatures for: {analysis.filename}")
        output_lines.append(f"# Generated from capa analysis ID: {analysis_id}")
        output_lines.append(f"# SHA-256: {analysis.file_hash}")
        output_lines.append(f"# Generated: {datetime.utcnow().isoformat()}Z")
        output_lines.append("")

        # Hash-based signatures
        output_lines.append("# Hash-based signatures (.hdb and .hsb)")
        output_lines.append("# Format: Hash:FileSize:MalwareName")
        output_lines.append(signatures['hash']['hdb'])
        output_lines.append(signatures['hash']['hsb'])
        output_lines.append("")

        # Body-based signatures (strings)
        if 'body' in signatures and signatures['body']:
            output_lines.append("# Body-based signatures (.ndb)")
            output_lines.append("# Format: MalwareName:TargetType:Offset:HexSignature")
            for sig in signatures['body']:
                output_lines.append(f"# Pattern: {sig['pattern'][:50]}... (entropy: {sig['entropy']:.2f})")
                output_lines.append(sig['signature'])
            output_lines.append("")

        # PE section hashes
        if 'pe_sections' in signatures and signatures['pe_sections']:
            output_lines.append("# PE section hash signatures (.mdb)")
            output_lines.append("# Format: SectionName:SectionHash:*:MalwareName")
            for sig in signatures['pe_sections']:
                output_lines.append(f"# Section: {sig['section']}")
                output_lines.append(sig['signature'])
            output_lines.append("")

        # Write to file
        sig_file = settings.results_dir / f"clamav_{analysis_id}.ndb"
        sig_file.write_text("\n".join(output_lines))

        logger.info(f"ClamAV signatures generated successfully for analysis {analysis_id}")

        # Return as downloadable file
        return FileResponse(
            sig_file,
            media_type="text/plain",
            filename=f"capa-analysis-{analysis_id}.ndb",
            headers={
                "Content-Disposition": f'attachment; filename="capa-analysis-{analysis_id}.ndb"'
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error generating ClamAV signatures: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate ClamAV signatures: {str(e)}")


@app.delete("/api/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Delete an analysis.

    Args:
        analysis_id: Analysis ID
        db: Database session

    Returns:
        Success message
    """
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Delete files
    try:
        file_path = Path(analysis.file_path)
        if file_path.exists():
            file_path.unlink()

        result_file = settings.results_dir / f"{analysis_id}.json"
        if result_file.exists():
            result_file.unlink()

        # Delete YARA file if it exists
        yara_file = settings.results_dir / f"yara_{analysis_id}.yar"
        if yara_file.exists():
            yara_file.unlink()
    except Exception as e:
        logger.error(f"Failed to delete files for analysis {analysis_id}: {e}")

    # Delete database entry
    db.delete(analysis)
    db.commit()

    return {"message": "Analysis deleted"}


# ============================================================================
# Static Files & Frontend
# ============================================================================

# Serve static files (web UI)
if Path("/app/static").exists():
    app.mount("/static", StaticFiles(directory="/app/static"), name="static")

    @app.get("/")
    async def root():
        """Serve the capa Explorer as the main UI."""
        from fastapi.responses import HTMLResponse

        explorer_index = Path("/app/static/explorer/index.html")
        if not explorer_index.exists():
            return {"message": "capa-server API", "docs": "/docs"}

        # Read the Explorer HTML
        with open(explorer_index, 'r') as f:
            html_content = f.read()

        # Fix asset paths to work with FastAPI static file serving
        html_content = html_content.replace('src="./assets/', 'src="/static/explorer/assets/')
        html_content = html_content.replace('href="./assets/', 'href="/static/explorer/assets/')
        html_content = html_content.replace('href="./favicon.ico"', 'href="/static/explorer/favicon.ico"')

        # Inject the bridge script before the closing body tag
        bridge_script = '<script src="/static/explorer/capa-server-bridge.js"></script>'
        html_content = html_content.replace('</body>', f'{bridge_script}</body>')

        return HTMLResponse(content=html_content)

    @app.get("/admin")
    async def admin_ui():
        """Serve the legacy admin/upload UI."""
        upload_index = Path("/app/static/index.html")
        if upload_index.exists():
            return FileResponse(upload_index)
        return {"message": "Admin UI not found", "docs": "/docs"}

    @app.get("/explorer")
    async def explorer():
        """Serve the capa Explorer Web UI with auto-load bridge."""
        from fastapi.responses import HTMLResponse

        explorer_index = Path("/app/static/explorer/index.html")
        if not explorer_index.exists():
            return {"message": "Explorer not found", "docs": "/docs"}

        # Read the Explorer HTML
        with open(explorer_index, 'r') as f:
            html_content = f.read()

        # Inject the bridge script before the closing body tag
        bridge_script = '<script src="/static/explorer/capa-server-bridge.js"></script>'
        html_content = html_content.replace('</body>', f'{bridge_script}</body>')

        return HTMLResponse(content=html_content)

    @app.get("/explorer/{analysis_id}")
    async def explorer_with_analysis(analysis_id: int, db: Session = Depends(get_db)):
        """Serve the capa Explorer Web UI with pre-loaded analysis results."""
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        if analysis.status != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed yet")

        # Serve a modified version of the Explorer that loads the analysis data
        # For now, redirect to /explorer and we'll handle data loading via JavaScript
        explorer_index = Path("/app/static/explorer/index.html")
        if explorer_index.exists():
            return FileResponse(explorer_index)
        return {"message": "Explorer not found", "docs": "/docs"}
else:
    @app.get("/")
    async def root():
        """API root when no web UI is available."""
        return {
            "message": "capa-server API",
            "docs": "/docs",
            "health": "/health",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)

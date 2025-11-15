"""ClamAV scanning functionality."""
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ClamAVScanner:
    """ClamAV virus scanner wrapper."""

    def __init__(self):
        """Initialize ClamAV scanner."""
        self.clamscan_path = "/usr/bin/clamscan"
        self._check_availability()

    def _check_availability(self) -> bool:
        """Check if ClamAV is available."""
        try:
            result = subprocess.run(
                [self.clamscan_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"ClamAV available: {result.stdout.strip()}")
                return True
            else:
                logger.warning("ClamAV not available")
                return False
        except Exception as e:
            logger.warning(f"ClamAV check failed: {e}")
            return False

    def scan_file(self, file_path: Path) -> Dict[str, any]:
        """
        Scan a file with ClamAV.

        Args:
            file_path: Path to file to scan

        Returns:
            Dictionary with scan results:
            {
                'scanned': bool,
                'status': 'clean' | 'infected' | 'error',
                'signature': str | None,
                'scan_time': datetime,
                'error': str | None
            }
        """
        result = {
            'scanned': False,
            'status': 'error',
            'signature': None,
            'scan_time': datetime.utcnow(),
            'error': None
        }

        try:
            if not file_path.exists():
                result['error'] = f"File not found: {file_path}"
                return result

            # Run clamscan
            # --no-summary: Don't print summary
            # --infected: Only print infected files
            # file_path: Path to scan
            proc = subprocess.run(
                [self.clamscan_path, "--no-summary", str(file_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            result['scanned'] = True

            # Return codes:
            # 0 = No virus found
            # 1 = Virus found
            # 2 = Error occurred

            if proc.returncode == 0:
                result['status'] = 'clean'
                logger.info(f"ClamAV scan: {file_path.name} - CLEAN")

            elif proc.returncode == 1:
                result['status'] = 'infected'

                # Parse signature from output
                # Format: "filename: Virus.Name FOUND"
                output = proc.stdout.strip()
                if "FOUND" in output:
                    # Extract signature name
                    parts = output.split(":")
                    if len(parts) >= 2:
                        sig_part = parts[-1].strip()
                        signature = sig_part.replace(" FOUND", "").strip()
                        result['signature'] = signature
                        logger.warning(f"ClamAV scan: {file_path.name} - INFECTED: {signature}")
                else:
                    result['signature'] = "Unknown"
                    logger.warning(f"ClamAV scan: {file_path.name} - INFECTED (unknown signature)")

            else:
                result['status'] = 'error'
                result['error'] = f"ClamAV error (code {proc.returncode}): {proc.stderr}"
                logger.error(f"ClamAV scan error: {proc.stderr}")

        except subprocess.TimeoutExpired:
            result['error'] = "Scan timeout (5 minutes exceeded)"
            logger.error(f"ClamAV scan timeout for {file_path.name}")

        except Exception as e:
            result['error'] = f"Scan exception: {str(e)}"
            logger.error(f"ClamAV scan exception: {e}", exc_info=True)

        return result

    def get_database_info(self) -> Dict[str, str]:
        """
        Get ClamAV database version information.

        Returns:
            Dictionary with database info
        """
        try:
            proc = subprocess.run(
                ["/usr/bin/sigtool", "--info=/var/lib/clamav/main.cvd"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if proc.returncode == 0:
                return {'database_info': proc.stdout}
            else:
                return {'error': 'Could not retrieve database info'}

        except Exception as e:
            return {'error': str(e)}


# Global scanner instance
scanner = ClamAVScanner()

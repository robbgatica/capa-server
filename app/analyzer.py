"""Capa analysis integration."""
import json
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from capa.exceptions import UnsupportedFormatError, UnsupportedArchError, UnsupportedOSError

from app.config import settings

logger = logging.getLogger(__name__)


class CapaAnalyzer:
    """Wrapper for capa analysis functionality."""

    def __init__(self, rules_path: Optional[Path] = None):
        """Initialize analyzer with rules."""
        self.rules_path = rules_path or settings.capa_rules_path
        self._rules = None

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def load_rules(self) -> int:
        """
        Load and count capa rules from the rules directory.

        Returns:
            Number of rule files found
        """
        if not self.rules_path.exists():
            logger.warning(f"Rules path does not exist: {self.rules_path}")
            self._rules = []
            return 0

        # Count .yml and .yaml files in the rules directory
        rule_files = list(self.rules_path.rglob("*.yml")) + list(self.rules_path.rglob("*.yaml"))
        self._rules = rule_files

        logger.info(f"Found {len(rule_files)} rule files in {self.rules_path}")
        return len(rule_files)

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a file with capa and return results.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary containing analysis results in capa's JSON format

        Raises:
            Various capa exceptions if analysis fails
        """
        logger.info(f"Starting analysis of {file_path}")

        # Ensure file_path is a Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            # Use capa's CLI via subprocess for simplicity and reliability
            # Run capa with JSON output
            cmd = [
                "capa",
                "-j",  # JSON output
                "-r", str(self.rules_path),  # Rules path
                "-s", "",  # No signatures (empty path to disable)
                str(file_path)  # Input file
            ]

            logger.info(f"Running capa: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )

            # Parse JSON output
            output = json.loads(result.stdout)

            logger.info(f"Analysis complete")
            return output

        except subprocess.TimeoutExpired:
            logger.error("Analysis timed out after 5 minutes")
            raise Exception("Analysis timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"Capa command failed: {e.stderr}")
            # Check for specific error types in stderr
            if "UnsupportedFormatError" in e.stderr:
                raise UnsupportedFormatError(e.stderr)
            elif "UnsupportedArchError" in e.stderr:
                raise UnsupportedArchError(e.stderr)
            elif "UnsupportedOSError" in e.stderr:
                raise UnsupportedOSError(e.stderr)
            else:
                raise Exception(f"Capa analysis failed: {e.stderr}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse capa output: {e}")
            raise Exception("Failed to parse analysis results")
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            raise

    def extract_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract summary information from capa results.

        Args:
            result: Full capa result dictionary

        Returns:
            Dictionary with summary information
        """
        summary = {
            "capa_version": result.get("meta", {}).get("version"),
            "capabilities_count": 0,
            "attack_techniques": [],
        }

        # Count capabilities
        if "rules" in result:
            summary["capabilities_count"] = len(result["rules"])

        # Extract ATT&CK techniques
        attack_set = set()
        for rule_name, rule_data in result.get("rules", {}).items():
            if "meta" in rule_data and "att&ck" in rule_data["meta"]:
                for attack in rule_data["meta"]["att&ck"]:
                    if isinstance(attack, dict):
                        attack_set.add(attack.get("id", ""))
                    else:
                        attack_set.add(str(attack))

        summary["attack_techniques"] = sorted(list(attack_set))

        return summary


# Global analyzer instance
analyzer = CapaAnalyzer()

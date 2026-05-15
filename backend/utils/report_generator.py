"""
Report Generator Service
Generates compliance audit reports in various formats
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import csv
from io import StringIO

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates compliance audit reports"""
    
    def __init__(self, data_dir: str = "./data/reports"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_metadata: List[Dict[str, Any]] = []
        self._load_metadata()
    
    def _load_metadata(self):
        """Load reports metadata from disk"""
        metadata_file = self.data_dir / "reports_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    self.reports_metadata = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load reports metadata: {e}")
                self.reports_metadata = []
    
    def _save_metadata(self):
        """Save reports metadata to disk"""
        metadata_file = self.data_dir / "reports_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(self.reports_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save reports metadata: {e}")
    
    def generate_report(
        self,
        report_type: str,
        standard: Optional[str],
        format: str,
        compliance_data: Dict[str, Any],
        violations: List[Dict[str, Any]],
        audit_trail: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a compliance audit report
        
        Args:
            report_type: Type of report (compliance, audit, assessment)
            standard: Specific standard or None for all
            format: Output format (json, csv, html)
            compliance_data: Compliance score and metrics
            violations: List of violations
            audit_trail: Audit trail events
            
        Returns:
            Report metadata including file path
        """
        timestamp = datetime.now(timezone.utc)
        report_id = f"report_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Generate report content based on format
        if format == 'json':
            content = self._generate_json_report(
                report_type, standard, compliance_data, violations, audit_trail
            )
            file_ext = 'json'
        elif format == 'csv':
            content = self._generate_csv_report(
                report_type, standard, compliance_data, violations
            )
            file_ext = 'csv'
        elif format == 'html':
            content = self._generate_html_report(
                report_type, standard, compliance_data, violations, audit_trail
            )
            file_ext = 'html'
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Save report to disk
        filename = f"{report_id}.{file_ext}"
        file_path = self.data_dir / filename
        
        if format == 'json':
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
        elif isinstance(content, str):
            with open(file_path, 'w') as f:
                f.write(content)
        else:
            raise ValueError(f"Invalid content type for format: {format}")
        
        # Create metadata
        metadata = {
            'id': report_id,
            'name': f"{report_type.title()} Report - {standard or 'All Standards'}",
            'type': report_type,
            'standard': standard,
            'format': format,
            'generated_at': timestamp.isoformat(),
            'file_path': str(file_path),
            'status': 'completed',
            'size_bytes': file_path.stat().st_size
        }
        
        self.reports_metadata.append(metadata)
        self._save_metadata()
        
        logger.info(f"Generated report: {report_id}")
        return metadata
    
    def _generate_json_report(
        self,
        report_type: str,
        standard: Optional[str],
        compliance_data: Dict[str, Any],
        violations: List[Dict[str, Any]],
        audit_trail: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate JSON format report"""
        report = {
            'report_metadata': {
                'type': report_type,
                'standard': standard,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'version': '1.0'
            },
            'executive_summary': {
                'overall_score': compliance_data.get('overall_score', 0),
                'total_violations': len(violations),
                'critical_violations': len([v for v in violations if v.get('severity') == 'critical']),
                'high_violations': len([v for v in violations if v.get('severity') == 'high']),
                'standards_assessed': list(compliance_data.get('standards', {}).keys())
            },
            'compliance_scores': compliance_data,
            'violations': violations,
            'audit_trail': audit_trail,
            'recommendations': self._generate_recommendations(violations)
        }
        
        return report
    
    def _generate_csv_report(
        self,
        report_type: str,
        standard: Optional[str],
        compliance_data: Dict[str, Any],
        violations: List[Dict[str, Any]]
    ) -> str:
        """Generate CSV format report"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Compliance Audit Report'])
        writer.writerow(['Generated:', datetime.now(timezone.utc).isoformat()])
        writer.writerow(['Standard:', standard or 'All Standards'])
        writer.writerow([])
        
        # Summary
        writer.writerow(['Summary'])
        writer.writerow(['Overall Score', f"{compliance_data.get('overall_score', 0) * 100:.1f}%"])
        writer.writerow(['Total Violations', len(violations)])
        writer.writerow([])
        
        # Violations
        writer.writerow(['Violations'])
        writer.writerow(['Control ID', 'Standard', 'Severity', 'Category', 'Description', 'Timestamp'])
        
        for violation in violations:
            writer.writerow([
                violation.get('control_id', ''),
                violation.get('standard', ''),
                violation.get('severity', ''),
                violation.get('category', ''),
                violation.get('description', ''),
                violation.get('timestamp', '')
            ])
        
        return output.getvalue()
    
    def _generate_html_report(
        self,
        report_type: str,
        standard: Optional[str],
        compliance_data: Dict[str, Any],
        violations: List[Dict[str, Any]],
        audit_trail: List[Dict[str, Any]]
    ) -> str:
        """Generate HTML format report"""
        overall_score = compliance_data.get('overall_score', 0) * 100
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Compliance Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2563eb; }}
        h2 {{ color: #1e40af; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #2563eb; color: white; }}
        tr:nth-child(even) {{ background-color: #f9fafb; }}
        .summary {{ background-color: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .critical {{ color: #dc2626; font-weight: bold; }}
        .high {{ color: #ea580c; font-weight: bold; }}
        .medium {{ color: #ca8a04; font-weight: bold; }}
        .low {{ color: #65a30d; font-weight: bold; }}
        .score {{ font-size: 48px; font-weight: bold; color: #2563eb; }}
    </style>
</head>
<body>
    <h1>Compliance Audit Report</h1>
    <p><strong>Generated:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p><strong>Standard:</strong> {standard or 'All Standards'}</p>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p class="score">{overall_score:.1f}%</p>
        <p><strong>Overall Compliance Score</strong></p>
        <p><strong>Total Violations:</strong> {len(violations)}</p>
        <p><strong>Critical:</strong> {len([v for v in violations if v.get('severity') == 'critical'])}</p>
        <p><strong>High:</strong> {len([v for v in violations if v.get('severity') == 'high'])}</p>
    </div>
    
    <h2>Standards Compliance</h2>
    <table>
        <tr>
            <th>Standard</th>
            <th>Score</th>
            <th>Controls</th>
            <th>Violations</th>
        </tr>
"""
        
        for std_name, std_data in compliance_data.get('standards', {}).items():
            score = std_data.get('score', 0) * 100
            html += f"""
        <tr>
            <td>{std_name}</td>
            <td>{score:.1f}%</td>
            <td>{std_data.get('controls', 0)}</td>
            <td>{std_data.get('violations', 0)}</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>Violations</h2>
    <table>
        <tr>
            <th>Control ID</th>
            <th>Standard</th>
            <th>Severity</th>
            <th>Category</th>
            <th>Description</th>
        </tr>
"""
        
        for violation in violations:
            severity = violation.get('severity', 'low')
            html += f"""
        <tr>
            <td>{violation.get('control_id', '')}</td>
            <td>{violation.get('standard', '')}</td>
            <td class="{severity}">{severity.upper()}</td>
            <td>{violation.get('category', '')}</td>
            <td>{violation.get('description', '')}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        return html
    
    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on violations"""
        recommendations = []
        
        critical_count = len([v for v in violations if v.get('severity') == 'critical'])
        if critical_count > 0:
            recommendations.append(
                f"Address {critical_count} critical violation(s) immediately to prevent compliance failures"
            )
        
        high_count = len([v for v in violations if v.get('severity') == 'high'])
        if high_count > 0:
            recommendations.append(
                f"Prioritize remediation of {high_count} high-severity violation(s) within 7 days"
            )
        
        # Group by category
        categories = {}
        for v in violations:
            cat = v.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            recommendations.append(
                f"Focus on {top_category[0]} controls - {top_category[1]} violations detected"
            )
        
        return recommendations
    
    def list_reports(
        self,
        standard: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List generated reports with optional filtering
        
        Args:
            standard: Filter by standard
            status: Filter by status
            limit: Maximum number of reports to return
            
        Returns:
            List of report metadata
        """
        reports = self.reports_metadata.copy()
        
        # Apply filters
        if standard:
            reports = [r for r in reports if r.get('standard') == standard]
        
        if status:
            reports = [r for r in reports if r.get('status') == status]
        
        # Sort by generated_at (newest first)
        reports.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        
        return reports[:limit]
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report metadata by ID"""
        for report in self.reports_metadata:
            if report['id'] == report_id:
                return report
        return None
    
    def delete_report(self, report_id: str) -> bool:
        """Delete a report"""
        report = self.get_report(report_id)
        if not report:
            return False
        
        # Delete file
        try:
            file_path = Path(report['file_path'])
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete report file: {e}")
            return False
        
        # Remove from metadata
        self.reports_metadata = [r for r in self.reports_metadata if r['id'] != report_id]
        self._save_metadata()
        
        logger.info(f"Deleted report: {report_id}")
        return True


# Singleton instance
_report_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """Get or create report generator singleton"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
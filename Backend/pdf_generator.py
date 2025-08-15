# pdf_generator.py
import io
import os
import datetime
from flask import Response
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


class ValidationReportGenerator:
    """
    Handles the generation of professional PDF validation reports using HTML/CSS.
    """

    def __init__(self, app_root_path: str | None = None):
        """
        Initialise the PDF generator.

        Args:
            app_root_path: The directory that contains the ``templates`` folder.
                           If omitted, the current working directory is used.
        """
        if app_root_path is None:
            app_root_path = os.getcwd()

        # Templates are expected in a sub‑folder named ``templates``.
        self.template_dir = os.path.join(app_root_path, "templates")
        if not os.path.isdir(self.template_dir):
            raise FileNotFoundError(f"Template directory not found: {self.template_dir!r}")

        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    # ------------------------------------------------------------------
    # Public API – the Flask view helper
    # ------------------------------------------------------------------
    def generate_pdf_response(self, data: dict) -> Response:
        """
        Create a Flask Response that streams the PDF to the client.

        Args:
            data: Must contain ``filename`` and ``results`` keys.

        Returns:
            flask.Response holding the PDF.
        """
        try:
            pdf_bytes = self._create_pdf_buffer(data)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(data.get("filename", "report"))[0]
            pdf_name = f"{base_name}_validation_report_{timestamp}.pdf"

            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={pdf_name}"
                },
            )
        except Exception as exc:
            raise RuntimeError(f"PDF generation failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _create_pdf_buffer(self, data: dict) -> bytes:
        """
        Render the template and convert it to PDF bytes.

        Returns:
            PDF file contents as bytes.
        """
        # Get or compute the stats
        stats = data.get("summary", self._calculate_stats(data["results"]))
        
        # Convert results to consistent format for template
        results = data["results"]
        formatted_results = []
        
        for result in results:
            if isinstance(result, (list, tuple)):
                # Handle complex nested structure where result[2] might be a dict
                name = str(result[0]) if len(result) > 0 else "Unknown Check"
                status = result[1] if len(result) > 1 else None
                
                # If the third element is a dict, it's already in our new format
                if len(result) > 2 and isinstance(result[2], dict):
                    message_data = result[2]
                    formatted_results.append({
                        "check_name": name,
                        "status": message_data.get("status", 
                            "passed" if status is False else "failed" if status is True else "error"),
                        "summary": message_data.get("summary", {"message": "No details available"}),
                        "details": message_data.get("details", []),
                        "errors": message_data.get("errors", [])
                    })
                else:
                    # Handle simple string message or missing message
                    message = str(result[2]) if len(result) > 2 else "No details available"
                    formatted_results.append({
                        "check_name": name,
                        "status": "passed" if status is False else "failed" if status is True else "error",
                        "summary": {"message": message},
                        "details": [],
                        "errors": []
                    })
            else:
                # Result is already in dictionary format
                formatted_results.append(result)
        
        # Build the Jinja2 context
        context = {
            "report_title": "Comsof Validation Report",
            "filename": data.get("filename", "Unknown"),
            "generation_date": data.get("summary", {}).get("completion_date", 
                datetime.datetime.now().strftime("%B %d, %Y at %H:%M:%S")),
            "results": formatted_results,
            "stats": {
                "total_checks": stats.get("total_tests", stats.get("total_checks", 0)),
                "passed_checks": stats.get("passed", stats.get("passed_checks", 0)),
                "failed_checks": stats.get("failed", stats.get("failed_checks", 0)),
                "error_checks": stats.get("errors", stats.get("error_checks", 0)),
                "completion_percentage": stats.get("completion_percentage", 100.0)
            },
        }

        # Grab the template
        template = self.env.get_template("validation_report.html")
        html_content = template.render(context)

        # Convert the HTML to PDF
        pdf_buffer = io.BytesIO()
        font_config = FontConfiguration()

        HTML(string=html_content).write_pdf(
            target=pdf_buffer,
            font_config=font_config,
            stylesheets=[CSS(string=self._get_css_styles())],
        )

        # Return the raw bytes, not the BytesIO object
        return pdf_buffer.getvalue()

    def _calculate_stats(self, results: list) -> dict:
        """
        Compute statistics for the report.
        
        Handles both formats:
        1. List of tuples: [(name, status, message), ...]
        2. List of dicts: [{"check_name": str, "status": str, ...}, ...]
        
        For tuple format:
        - status True → failed
        - status False → passed
        - status None → error
        
        For dict format:
        - status "failed" → failed
        - status "passed" → passed
        - status "error" → error
        """
        total = len(results)
        
        # Detect format (tuple or dict)
        if results and isinstance(results[0], (list, tuple)):
            # Old tuple format - safely get status from index 1 if available
            passed = sum(1 for r in results if len(r) > 1 and r[1] is False)
            failed = sum(1 for r in results if len(r) > 1 and r[1] is True)
            errors = sum(1 for r in results if len(r) <= 1 or r[1] is None)
            completion = (
                round(
                    sum(1 for r in results if len(r) > 1 and r[1] is not None)
                    / total
                    * 100,
                    1,
                )
                if total
                else 0.0
            )
        else:
            # New dict format
            passed = sum(1 for result in results if result.get("status") == "passed")
            failed = sum(1 for result in results if result.get("status") == "failed")
            errors = sum(1 for result in results if result.get("status") == "error")
            completion = (
                round(
                    sum(1 for result in results if result.get("status") != "error")
                    / total
                    * 100,
                    1,
                )
                if total
                else 0.0
            )

        return {
            "total_checks": total,
            "passed_checks": passed,
            "failed_checks": failed,
            "error_checks": errors,
            "completion_percentage": completion,
        }

    def _get_css_styles(self) -> str:
        """
        Return the full CSS string that styles the PDF report.
        """
        return """
            @page {
                size: A4;
                margin: 1cm;

                @top-left {
                    content: "";
                    background: #1976d2;
                    height: 0.6cm;
                    width: 0.6cm;
                    position: absolute;
                    top: 0;
                    left: 0;
                }

                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-family: Inter, sans-serif;
                    font-size: 8pt;
                    color: #6c757d;
                    margin-top: 0.5cm;
                }
            }

            body {
                font-family: Inter, sans-serif;
                font-size: 10pt;
                line-height: 1.6;
                color: #343a40;
                background: #fff;
                margin: 0;
                padding: 1.5cm 1.5cm 2.5cm 1.5cm;
            }

            /* Header */
            .header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 1.5cm;
                padding-bottom: 1cm;
                border-bottom: 1px solid #e9ecef;
            }
            .company-info{flex:1;}
            .company-name{
                font-size:22pt;font-weight:700;color:#212529;
                margin:0 0 0.2cm 0;letter-spacing:-0.5px;
            }
            .company-subtitle{
                font-size:11pt;font-weight:400;color:#6c757d;
                margin:0;text-transform:uppercase;letter-spacing:1px;
            }
            .report-meta{text-align:right;}
            .report-title{
                font-size:18pt;font-weight:600;color:#212529;
                margin:0 0 0.2cm 0;
            }
            .document-info{
                font-size:9pt;color:#6c757d;margin:0;
            }

            /* Summary */
            .summary-section{
                background:#f8f9fa;border-radius:8px;padding:0.8cm;
                margin-bottom:1.5cm;position:relative;overflow:hidden;
            }
            .summary-section::before{
                content:"";
                position:absolute;
                top:0;left:0;height:100%;width:5px;
                background:#1976d2;
            }
            .section-title{
                font-size:14pt;font-weight:600;color:#212529;
                margin-bottom:0.5cm;display:flex;align-items:center;
            }
            .section-title::before{
                content:"";
                display:inline-block;width:6px;height:6px;
                border-radius:50%;background:#1976d2;margin-right:8px;
            }

            /* Stats */
            .stats-grid{
                display:grid;
                grid-template-columns:repeat(4,1fr);
                gap:0.8cm;margin-bottom:0.8cm;
            }
            .stat-card{
                background:#fff;border-radius:6px;padding:0.6cm;
                box-shadow:0 2px 6px rgba(0,0,0,.05);
                text-align:center;border-top:3px solid;
            }
            .stat-total{border-top-color:#1976d2;}
            .stat-passed{border-top-color:#28a745;}
            .stat-failed{border-top-color:#dc3545;}
            .stat-error{border-top-color:#ffc107;}
            .stat-number{
                font-size:20pt;font-weight:700;margin:0 0 0.2cm 0;
            }
            .stat-label{
                font-size:9pt;color:#6c757d;text-transform:uppercase;
                letter-spacing:1px;margin:0;
            }

            /* Progress */
            .progress-container{
                background:#fff;border-radius:6px;padding:0.6cm;
                box-shadow:0 2px 6px rgba(0,0,0,.05);
            }
            .progress-title{
                font-size:10pt;font-weight:600;color:#212529;margin:0 0 0.4cm 0;
            }
            .progress-bar{
                height:10px;background:#e9ecef;border-radius:5px;
                overflow:hidden;
            }
            .progress-fill{
                height:100%;background:linear-gradient(90deg,#1976d2,#2196f3);
                border-radius:5px;
            }
            .progress-percentage{
                text-align:right;font-size:9pt;color:#6c757d;margin-top:0.2cm;
            }

            /* Results */
            .results-section{margin-bottom:1cm;}
            .check{
                margin-bottom:0.8cm;page-break-inside:avoid;
            }
            .check-header{
                display:flex;justify-content:space-between;
                align-items:center;margin-bottom:0.3cm;
            }
            .check-title{
                font-size:12pt;font-weight:600;color:#212529;margin:0;
            }
            .status{
                display:inline-block;padding:3px 12px;border-radius:20px;
                font-weight:600;font-size:9pt;color:white;
                text-transform:uppercase;letter-spacing:.5px;
            }
            .status-passed{background:#28a745;}
            .status-failed{background:#dc3545;}
            .status-error{background:#ffc107;color:#212529;}
            .check-content{
                background:#fff;border-radius:6px;padding:0.6cm;
                border-left:3px solid #e9ecef;
            }
            .check-message{margin:0;line-height:1.6;}
            .check-details{
                font-family:Fira Code,monospace;font-size:9pt;
                background:#f8f9fa;padding:0.6cm;margin-top:0.4cm;
                border-radius:4px;overflow-wrap:break-word;
                white-space:pre-wrap;border-left:2px solid #dee2e6;
            }

            /* Footer */
            .footer{
                position:fixed;bottom:0;left:0;right:0;
                padding:0.5cm 1.5cm;background:#f8f9fa;
                border-top:1px solid #e9ecef;font-size:8pt;
                color:#6c757d;text-align:center;
            }

            .critical{
                color:#dc3545;font-weight:600;
                background:rgba(220,53,69,.1);padding:2px 4px;
                border-radius:3px;
            }
            .warning{
                color:#ffc107;font-weight:600;
                background:rgba(255,193,7,.1);padding:2px 4px;
                border-radius:3px;
            }
            .divider{
                height:1px;background:#e9ecef;margin:0.8cm 0;
            }
        """

# ----------------------------------------------------------------------
# Convenience wrapper for Flask views
# ----------------------------------------------------------------------
def generate_validation_report_pdf(data: dict, app_root_path: str | None = None):
    """
    Generate a Flask Response that contains the PDF.

    Args:
        data: Dictionary with ``filename`` and ``results`` keys.
        app_root_path: Path to the folder that holds the ``templates`` sub‑folder.
                       If omitted, the current working directory is used.

    Returns:
        flask.Response that streams the PDF.
    """
    generator = ValidationReportGenerator(app_root_path)
    return generator.generate_pdf_response(data)
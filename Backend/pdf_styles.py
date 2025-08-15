# pdf_styles.py
# --------------------------------------------------------------------------
#  Enhanced ReportLab paragraph styles for professional PDF reports
# --------------------------------------------------------------------------
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def get_pdf_styles() -> dict:
    """
    Return a dict mapping style names to ReportLab ParagraphStyle objects.
    Enhanced with professional styling for section-based layout.
    """
    return {
        # ------------------------------------------------------------------
        #  Header styles
        # ------------------------------------------------------------------
        'company_name': ParagraphStyle(
            name='CompanyName',
            fontName='Helvetica-Bold',
            fontSize=24,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#1976d2"),  # Professional blue
            spaceBefore=0,
            spaceAfter=4,
        ),

        'company_subtitle': ParagraphStyle(
            name='CompanySubtitle',
            fontName='Helvetica',
            fontSize=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#666666"),
            spaceBefore=0,
            spaceAfter=0,
        ),

        # ------------------------------------------------------------------
        #  Document title and metadata
        # ------------------------------------------------------------------
        'document_title': ParagraphStyle(
            name='DocumentTitle',
            fontName='Helvetica-Bold',
            fontSize=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2c3e50"),
            spaceBefore=20,
            spaceAfter=8,
        ),

        'document_subtitle': ParagraphStyle(
            name='DocumentSubtitle',
            fontName='Helvetica',
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#7f8c8d"),
            spaceBefore=0,
            spaceAfter=6,
        ),

        'metadata': ParagraphStyle(
            name='Metadata',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#95a5a6"),
            spaceBefore=0,
            spaceAfter=30,
        ),

        # ------------------------------------------------------------------
        #  Section headers for check results
        # ------------------------------------------------------------------
        'section_header': ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=16,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#34495e"),
            spaceBefore=25,
            spaceAfter=12,
            borderWidth=0,
            borderColor=colors.HexColor("#bdc3c7"),
            leftIndent=0,
        ),

        'check_title': ParagraphStyle(
            name='CheckTitle',
            fontName='Helvetica-Bold',
            fontSize=13,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#2c3e50"),
            spaceBefore=18,
            spaceAfter=6,
            leftIndent=0,
        ),

        # ------------------------------------------------------------------
        #  Status badges with better styling
        # ------------------------------------------------------------------
        'status_passed': ParagraphStyle(
            name='StatusPassed',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.white,
            backColor=colors.HexColor("#27ae60"),  # Success green
            alignment=TA_CENTER,
            borderPadding=(6, 3, 6, 3),
            borderRadius=4,
        ),

        'status_failed': ParagraphStyle(
            name='StatusFailed',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.white,
            backColor=colors.HexColor("#e74c3c"),  # Error red
            alignment=TA_CENTER,
            borderPadding=(6, 3, 6, 3),
            borderRadius=4,
        ),

        'status_error': ParagraphStyle(
            name='StatusError',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.white,
            backColor=colors.HexColor("#f39c12"),  # Warning orange
            alignment=TA_CENTER,
            borderPadding=(6, 3, 6, 3),
            borderRadius=4,
        ),

        # ------------------------------------------------------------------
        #  Content styles
        # ------------------------------------------------------------------
        'check_message': ParagraphStyle(
            name='CheckMessage',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2c3e50"),
            spaceBefore=4,
            spaceAfter=12,
            leftIndent=20,
            rightIndent=10,
        ),

        'check_details': ParagraphStyle(
            name='CheckDetails',
            fontName='Courier',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#34495e"),
            spaceBefore=6,
            spaceAfter=12,
            leftIndent=30,
            rightIndent=10,
            backColor=colors.HexColor("#f8f9fa"),
            borderPadding=(8, 6, 8, 6),
        ),

        # ------------------------------------------------------------------
        #  Summary styles
        # ------------------------------------------------------------------
        'summary_header': ParagraphStyle(
            name='SummaryHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#2c3e50"),
            spaceBefore=20,
            spaceAfter=10,
        ),

        'summary_item': ParagraphStyle(
            name='SummaryItem',
            fontName='Helvetica',
            fontSize=11,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#34495e"),
            spaceBefore=3,
            spaceAfter=3,
            leftIndent=15,
        ),

        # ------------------------------------------------------------------
        #  Footer and page numbering
        # ------------------------------------------------------------------
        'footer': ParagraphStyle(
            name='Footer',
            fontName='Helvetica',
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#95a5a6"),
        ),

        # ------------------------------------------------------------------
        #  Divider line style (for visual separation)
        # ------------------------------------------------------------------
        'divider': ParagraphStyle(
            name='Divider',
            fontName='Helvetica',
            fontSize=1,
            spaceBefore=15,
            spaceAfter=15,
            backColor=colors.HexColor("#ecf0f1"),
        ),

        # ------------------------------------------------------------------
        #  Legacy styles (kept for compatibility)
        # ------------------------------------------------------------------
        'title': ParagraphStyle(
            name='Title',
            fontName='Helvetica-Bold',
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.black,
        ),

        'filename': ParagraphStyle(
            name='Filename',
            fontName='Helvetica',
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.black,
        ),

        'date': ParagraphStyle(
            name='Date',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=24,
            textColor=colors.black,
        ),

        'section': ParagraphStyle(
            name='Section',
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.black,
        ),

        'result_title': ParagraphStyle(
            name='ResultTitle',
            fontName='Helvetica-Bold',
            fontSize=12,
            spaceAfter=3,
            textColor=colors.black,
        ),

        'normal': ParagraphStyle(
            name='Normal',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.black,
        ),

        'error': ParagraphStyle(
            name='Error',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.red,
        ),

        'header': ParagraphStyle(
            name='Header',
            fontName='Helvetica-Bold',
            fontSize=16,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#333333"),
            spaceAfter=6,
        ),

        'table_header': ParagraphStyle(
            name='TableHeader',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.white,
            backColor=colors.HexColor("#424242"),
            alignment=TA_CENTER,
        ),
    }
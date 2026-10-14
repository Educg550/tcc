from fpdf import FPDF

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from PIL import Image
from io import BytesIO
from datetime import datetime

FILE_PATH = "assets"

class DocumentTemplate(FPDF):
    def __init__(self, year):
        super().__init__()
        self.year = year

    def header(self):
        w = 25
        self.set_margin(25)
        self.set_top_margin(15)
        self.image("assets/logo.png", x=25, y=15, w=35)
        self.image("assets/usp.png", x=self.w - self.r_margin - w, y=15, w=w)
        self.set_font("Arial", "", 20)
        self.cell(0, 10, "", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()} | {datetime.now().date()}", 0, 0, "C")

    def add_title(self, title):
        self.set_font("Arial", "", 20)
        self.set_text_color(7, 55, 99)
        self.multi_cell(0, 10, title.upper(), 0, "C")
        self.cell(0, 10, "", 0, 1, "C")
        self.set_font("Arial", "", 15)
        self.set_text_color(102, 102, 102)
        self.multi_cell(0, 10, f"Ingresso em {self.year}".upper(), 0, "C")
        self.set_font("Arial", "", 15)
        self.ln(5)
        self.set_text_color(0, 0, 0)

    def add_subtitle(self, subtitle):
        self.ln(5)
        self.set_font("Times", "B", 12)
        self.set_text_color(7, 55, 99)
        self.cell(0, 10, subtitle, ln=True)
        self.set_text_color(0, 0, 0)

    def add_content(self, content):
        self.set_font("Arial", "", 11)
        self.write_html(f"<p align='justify' style='line-height:2.0;'>{content}</p>")
        self.ln(1)

    def add_plot(self, figure):
        y_current = self.get_y()
        height_page = self.h
        margin_bottom_page = self.b_margin

        space_bottom = height_page - y_current - margin_bottom_page

        width = self.w*0.75

        canvas = FigureCanvas(figure)
        canvas.draw()

        w, h = figure.canvas.get_width_height()
        buf, _ = canvas.print_to_buffer()
        img = Image.frombytes("RGBA", (w, h), buf)
        img = img.convert("RGB")

        img_buffer = BytesIO()
        img.save(img_buffer, format="JPEG")
        img_buffer.seek(0)

        with Image.open(img_buffer) as img:
            w, h = img.size
            height_calc = (h / w) * width
            if height_calc > space_bottom:
                self.add_page()
                y_current = self.get_y()
        self.image(img_buffer, x=self.w*0.25/2, y=y_current, w=width)
        self.set_y(y_current + height_calc)

    def add_table(self, header, data, col_widths):
        self.ln(5)
        row_height = 10

        self.set_font("Arial", "B", 11)
        self.set_fill_color(200, 200, 200)
        for i, col_name in enumerate(header):
            self.cell(col_widths[i], row_height, col_name.upper(), border=1, align="C", fill=True)
        self.ln(row_height)

        self.set_font("Arial", "", 11)
        fill = False
        self.set_fill_color(255, 255, 255)
        if len(data) <= 0:
            for i, item in enumerate(header):
                self.cell(col_widths[i], row_height, "--", border=1, align="C", fill=True)
            self.ln(row_height)

        for row in data:
            if fill:
                self.set_fill_color(230, 230, 230)
            else:
                self.set_fill_color(255, 255, 255)
            for i, item in enumerate(row):
                self.cell(col_widths[i], row_height, str(item), border=1, align="C", fill=True)
            self.ln(row_height)
            fill = not fill
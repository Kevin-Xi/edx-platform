# -*- coding: utf-8 -*-
from PIL import Image
from reportlab.lib import colors

from django.conf import settings
from django.utils.translation import ugettext as _
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus.tables import Table, TableStyle

import locale
import warnings


class UnicodeProperty(object):
    _attrs = ()

    def __setattr__(self, key, value):
        if key in self._attrs:
            value = unicode(value)
        self.__dict__[key] = value

class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if num_pages > 1:
                self.draw_page_number(num_pages)
            Canvas.showPage(self)
        Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFontSize(7)
        self.drawRightString(200*mm, 12*mm,
            _("Page %(page_number)d of %(page_count)d") % {"page_number": self._pageNumber, "page_count": page_count})


class SimpleInvoice(UnicodeProperty):
    def __init__(self, context):
        self.items_data = context['items_data']
        self.id = context['id']
        self.date = context['date']
        self.is_invoice = context['is_invoice']
        self.total_cost = context['total_cost']
        self.logo_path = context['logo_path']
        self.cobrand_logo_path = context['cobrand_logo_path']
        self.payment_received = context['payment_received'] if 'payment_received' in context else ''
        self.balance = context['balance'] if 'balance' in context else ''
        self.currency = settings.PAID_COURSE_REGISTRATION_CURRENCY[1]
        self.tax_id = context['tax_id']
        self.disclaimer_text = context['disclaimer_text']
        self.billing_address_text = context['billing_address_text']
        self.tax_label = context['tax_label']
        self.terms_and_conditions = context['terms_and_conditions']
        self.footer_text = context['footer_text']

    def prepare_invoice_draw(self):
        self.MARGIN = 15 * mm
        self.page_width = letter[0]
        self.page_height = letter[1]
        self.min_clearance = 3 * mm

        self.pdf = NumberedCanvas(self.filename, pagesize=letter)

        self.pdf.setFontSize(15)
        self.pdf.setStrokeColorRGB(0.5, 0.5, 0.5)
        self.pdf.setLineWidth(0.353 * mm)

    def gen(self, filename):
        self.filename = filename

        self.prepare_invoice_draw()

        self.draw_borders()
        y_pos = self.draw_logos()
        self.second_page_available_height = y_pos - self.MARGIN - self.min_clearance
        self.second_page_start_y_pos = y_pos

        y_pos = self.draw_title(y_pos)
        self.first_page_available_height = y_pos - self.MARGIN - self.min_clearance

        y_pos = self.draw_course_info(y_pos)
        y_pos = self.show_totals(y_pos)
        self.draw_footer(y_pos)
        # self.pdf.setFillColorRGB(0, 0, 0)

        self.pdf.showPage()
        self.pdf.save()

    #############################################################
    ## Draw methods
    #############################################################

    def draw_borders(self):
        # Borders
        self.pdf.rect(self.MARGIN, self.MARGIN,
                      self.page_width - (self.MARGIN * 2), self.page_height - (self.MARGIN * 2),
                      stroke=True, fill=False)

    def draw_logos(self):
        img_height = 12 * mm
        horizontal_padding_from_border = 9 * mm
        vertical_padding_from_border = 11 * mm
        img_y_pos = self.page_height - (self.MARGIN + vertical_padding_from_border + img_height)

        if self.cobrand_logo_path:
            img = Image.open(self.cobrand_logo_path)
            img_width = float(img.size[0]) / (float(img.size[1])/img_height)
            self.pdf.drawImage(self.cobrand_logo_path, self.MARGIN + horizontal_padding_from_border, img_y_pos, img_width, img_height, mask='auto')

        if self.logo_path:
            img = Image.open(self.logo_path)
            img_width = float(img.size[0]) / (float(img.size[1])/img_height)
            self.pdf.drawImage(self.logo_path, self.page_width - (self.MARGIN + horizontal_padding_from_border + img_width), img_y_pos, img_width, img_height, mask='auto')

        return img_y_pos - self.min_clearance

    def draw_title(self, y_pos):
        if self.is_invoice:
            title = 'INVOICE'
            id_label = 'Invoice'
        else:
            title = 'RECEIPT'
            id_label = 'Order'

        vertical_padding = 5 * mm

        # Draw Title "RECEIPT" OR "INVOICE"
        font_size = 21
        self.pdf.setFontSize(font_size)
        self.pdf.drawCentredString(self.page_width/2, y_pos - vertical_padding - font_size/2, title)

        y_pos = y_pos - vertical_padding - font_size/2 - self.min_clearance

        font_size = 10
        self.pdf.setFontSize(font_size)

        horizontal_padding_from_border = 9 * mm

        y_pos = y_pos - font_size/2 - vertical_padding
        # Draw Order/Invoice No.
        self.pdf.drawString(self.MARGIN + horizontal_padding_from_border, y_pos, _(u'{id_label} # {id}'.format(id_label=id_label, id=self.id)))

        # Draw Date
        self.pdf.drawRightString(self.page_width - (self.MARGIN + horizontal_padding_from_border) , y_pos, _(u'Date {date}'.format(date=self.date)))

        return y_pos - self.min_clearance

    def draw_course_info(self, y_pos):
        style = getSampleStyleSheet()['Normal']
        data = [['', 'Description', 'Quantity', 'List Price\nper item', 'Discount\nper item', 'Amount', '']]
        for row in self.items_data:
            for i in range(1):
                data.append([
                    '',
                    Paragraph(row['item_name'], style),
                    row['quantity'],
                    '{currency}{price}'.format(price=row['list_price'], currency=self.currency),
                    '{currency}{price}'.format(price=row['discount'], currency=self.currency),
                    '{currency}{price}'.format(price=row['total'], currency=self.currency),
                    ''
                ])

        padding = 7 * mm
        desc_col_width = 60 * mm
        qty_col_width = 26 * mm
        list_price_col_width = 21 * mm
        discount_col_width = 21 * mm
        amount_col_width = 40 * mm
        items_table=Table(data,[padding, desc_col_width, qty_col_width, list_price_col_width, discount_col_width, amount_col_width, padding],  splitByRow=1, repeatRows=1)

        items_table.setStyle(TableStyle([
            ('ALIGN',(3,1),(5,-1),'RIGHT'),
            ('RIGHTPADDING', (5,1), (5,-1), 7*mm),
            ('ALIGN',(2,0),(-1,0),'CENTER'),
            ('ALIGN',(1,0),(0,0),'LEFT'),
            ('ALIGN',(1,1),(1,-1),'LEFT'),
            ('ALIGN',(2,1),(2,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),2*mm),
            ('BOTTOMPADDING',(0,0),(-1,-1),2*mm),
            ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
            ('LINEBELOW', (0,0), (-1,0), 1.00, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 1.00, colors.black),
            ('INNERGRID', (1,1), (-2,-1), 0.50, colors.black),
        ]))
        items_table.wrap(0,0)


        first_page_top = y_pos

        split_tables = items_table.split(0, self.first_page_available_height)
        last_table_height = 0
        table_left_padding = 2 * mm
        is_on_first_page = True
        if len(split_tables)>1:
            split_table = split_tables[0]
            split_table.wrap(0,0)
            split_table.drawOn(self.pdf, self.MARGIN + table_left_padding, first_page_top - split_table._height)

            self.prepare_new_page()
            is_on_first_page = False
            split_tables = split_tables[1].split(0, self.second_page_available_height)
            while len(split_tables) > 1:
                split_table = split_tables[0]
                split_table.wrap(0,0)
                split_table.drawOn(self.pdf, self.MARGIN + table_left_padding, self.second_page_start_y_pos - split_table._height)

                self.prepare_new_page()
                split_tables = split_tables[1].split(0, self.second_page_available_height)
            split_table = split_tables[0]
            split_table.wrap(0,0)
            split_table.drawOn(self.pdf, self.MARGIN + table_left_padding, self.second_page_start_y_pos - split_table._height)
            last_table_height = split_table._height
        else:
            split_table = split_tables[0]
            split_table.wrap(0,0)
            split_table.drawOn(self.pdf, self.MARGIN + table_left_padding, first_page_top -split_table._height)
            last_table_height = split_table._height

        if is_on_first_page:
            return first_page_top - last_table_height - self.min_clearance
        else:
            return self.second_page_start_y_pos - last_table_height - self.min_clearance

    def prepare_new_page(self):
        self.pdf.showPage()
        self.draw_borders()
        y_pos = self.draw_logos()
        return y_pos

    def show_totals(self, y_pos):
        data = [
            ['Total', '{currency}{price}'.format(currency=self.currency, price=self.total_cost)],
            ['Payment Received', '{currency}{price}'.format(currency=self.currency, price=self.payment_received)],
            ['Balance', '{currency}{price}'.format(currency=self.currency, price=self.balance)],
            ['', '{tax_label}:  {tax_id}'.format(tax_label=self.tax_label, tax_id=self.tax_id)]
        ]

        heights = 8*mm
        t=Table(data,40*mm, heights)

        t.setStyle(TableStyle([
            ('ALIGN',(0,0),(-1,-1),'RIGHT'),
            ('RIGHTPADDING', (-1,0), (-1,-2), 7*mm),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
            ('GRID', (-1,0), (-1,-2), 0.50, colors.black),
            ('BACKGROUND', (-1,0), (-1,-2), colors.lightgrey),
        ]))
        t.wrap(0,0)
        left_padding = 97 * mm
        if y_pos - (self.MARGIN + self.min_clearance) <= t._height:
            self.prepare_new_page()
            t.drawOn(self.pdf, self.MARGIN + left_padding, self.second_page_start_y_pos - t._height)
            return self.second_page_start_y_pos - t._height - self.min_clearance
        else:
            t.drawOn(self.pdf, self.MARGIN + left_padding, y_pos - t._height)
            return y_pos - t._height - self.min_clearance


    def draw_footer(self, y_pos):

        style = getSampleStyleSheet()['Normal']
        style.fontSize = 8

        footer_para = Paragraph(self.footer_text.replace("\n", "<br/>"), style)
        disclaimer_para = Paragraph(self.disclaimer_text.replace("\n", "<br/>"), style)
        billing_address_para = Paragraph(self.billing_address_text.replace("\n", "<br/>"), style)

        data= [
            [footer_para],
            ['Disclaimer'],
            [disclaimer_para],
            ['Billing Address'],
            [billing_address_para]
        ]

        footer_style = [
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TEXTCOLOR',(0,0),(-1,-1),colors.black),
            ('BACKGROUND', (0,0), (0,0), colors.lightgrey),
            ('LEFTPADDING', (0,0), (0,0), 5*mm),
            ('RIGHTPADDING', (0,0), (0,0), 5*mm),
            ('GRID', (0,0), (0,0), 0.50, colors.black),
            ('BACKGROUND', (0,2), (0,2), colors.lightgrey),
            ('LEFTPADDING', (0,2), (0,2), 5*mm),
            ('RIGHTPADDING', (0,2), (0,2), 5*mm),
            ('GRID', (0,2), (0,2), 0.50, colors.black),
            ('BACKGROUND', (0,4), (0,4), colors.lightgrey),
            ('LEFTPADDING', (0,4), (0,4), 5*mm),
            ('RIGHTPADDING', (0,4), (0,4), 5*mm),
            ('GRID', (0,4), (0,4), 0.50, colors.black),

        ]

        if (self.is_invoice):
            terms_conditions_para = Paragraph(self.terms_and_conditions.replace("\n", "<br/>"), style)
            data.append(['TERMS AND CONDITIONS'])
            data.append([terms_conditions_para])
            footer_style.append(('LEFTPADDING', (0,6), (0,6), 5*mm))
            footer_style.append(('RIGHTPADDING', (0,6), (0,6), 5*mm))

        t=Table(data, 176*mm)

        t.setStyle(TableStyle(footer_style))
        t.wrap(0,0)

        if y_pos - ( self.MARGIN + self.min_clearance ) <= t._height:
            self.prepare_new_page()

        t.drawOn(self.pdf, self.MARGIN + 5 * mm, self.MARGIN + 5 * mm)




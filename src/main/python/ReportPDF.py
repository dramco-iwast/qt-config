from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, SimpleDocTemplate, Spacer, TableStyle, Image
from reportlab.lib import colors

import datetime


class Report(object):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, title_doc, report_title):
        """Constructor"""
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
        self.title_doc = title_doc
        self.idr = 0

        self.report_title = report_title
        today = datetime.datetime.today()
        month = str(today.month)
        day = str(today.day)
        if today.month < 10:
            month = str("0" + str(today.month))
        if today.day < 10:
            day = str("0" + str(today.day))
        self.report_date = str(day + "/" + month + "/" + str(today.year))
        self.data_date = "XX/XX/XX"
        seq = int(today.strftime("%Y%m%d%H%M%S"))
        self.set_idr(seq)

        self.board_name = ['Motherboard', '', '', '', '', '', '']
        self.data_acc = False
        self.spreading_factor = 0

        colonnes = 6
        lignes = 64
        self.data_value = [['/'] * colonnes for _ in range(lignes)]
        self.estimation_value = [0, 0, 0, 0]

        self.c = canvas.Canvas(self.title_doc, pagesize=A4, )

    # ----------------------------------------------------------------------
    def run(self):
        """
        Run the report
        """
        err = "ok"
        self.createFirstSection()
        nb = self.createSecondSection()
        self.create_third_section(nb)

        self.c.showPage()
        try:
            self.c.save()
        except:
            err = "saving operation not possible"
        return err

    # ----------------------------------------------------------------------
    def createFirstSection(self):
        """
        Create the header section
        """
        style = self.styles['Normal']
        justified = ParagraphStyle(name="justified", alignment=TA_JUSTIFY)

        title = str("<b>" + self.report_title + "</b>")
        p = Paragraph(title, style)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, 60, 780)

        self.c.line(60, 773, 540, 773)
        self.c.line(60, 770, 540, 770)

        date_report = str("Report date: " + self.report_date)
        p = Paragraph(date_report, style)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, 100, 740)

        date_data = str("Date of measurements: " + self.data_date)
        p = Paragraph(date_data, style)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, 100, 720)

        spreading_fact = str("Spreading factor: " + str(self.get_spreading_factor()))
        p = Paragraph(spreading_fact, style)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, 100, 690)

        data_acc = str("Data accumulation: " + str(self.get_data_acc()))
        p = Paragraph(data_acc, style)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, 100, 670)

        idr = str("ID: "+str(self.get_idr()))
        p = Paragraph(idr, style)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, 445, 780)

        #im = Image('src/main/resources/dramco.png', width=75, height=75)
        #im.drawOn(self.c, 445, 680)

    # ----------------------------------------------------------------------
    def createSecondSection(self):
        """
        Create the power profile
        """

        self.c.line(60, 657, 540, 657)

        right = ParagraphStyle(name="right", alignment=TA_RIGHT, fontSize=8)
        center = ParagraphStyle(name="center", alignment=TA_CENTER)
        left = ParagraphStyle(name="left", alignment=TA_LEFT, )

        colonnes = 7
        lignes = 30

        table = [[''] * colonnes for _ in range(lignes)]

        table[0][0] = Paragraph("<b>Mode</b>", center)
        table[0][1] = Paragraph("<b>Number</b>", center)
        table[0][2] = Paragraph("<b>Aver. Current [uA]</b>", center)
        table[0][3] = Paragraph("<b>Time [ms]</b>", center)
        table[0][4] = Paragraph("<b>Total Time [ms]</b>", center)
        table[0][5] = Paragraph("<b>Energy [uWh]</b>", center)
        table[0][6] = Paragraph("<b>Total Energy [uWh]</b>", center)

        # All Modes
        lign = 1
        lign2 = 1
        idx = 0
        flag = True
        data_to_print = False
        first_page = True
        mode_list = ['Sleep',
                     'Wake-Up MB.',
                     'Thresh. not Exceed.',
                     'Thresh. Exceed',
                     'Polling',
                     'Storing Data',
                     'Status Msg',
                     'Sending Msg.']
        total_index = []

        while flag is True:
            table[lign][0] = Paragraph(mode_list[idx], left)
            lign += 1
            total_value = 0
            for idc in range(len(self.board_name)):
                if self.get_data_value(lign2-1, 3) is not '/':
                    data_to_print = True
                    table[lign][0] = Paragraph(self.get_board_name(idc), right)
                    table[lign][1] = Paragraph(str(self.get_data_value(lign2-1, 0)), right)
                    table[lign][2] = Paragraph(str(self.get_data_value(lign2-1, 1)), right)
                    table[lign][3] = Paragraph(str(self.get_data_value(lign2-1, 2)), right)
                    table[lign][4] = Paragraph(str(self.get_data_value(lign2-1, 3)), right)
                    table[lign][5] = Paragraph(str(self.get_data_value(lign2-1, 4)), right)
                    table[lign][6] = Paragraph(str(self.get_data_value(lign2-1, 5)), right)
                    total_value += self.get_data_value(lign2-1, 5)
                    lign += 1
                lign2 += 1

            table[lign][0] = Paragraph("<b>Total</b>", left)
            table[lign][6] = Paragraph("<b>"+str(round(total_value,2))+"</b>", right)
            total_index.append(lign)
            lign += 1

            if mode_list[idx] == 'Sending Msg.':
                flag = False
            else:
                idx += 1
            if lign >= 25:
                table = Table(table, colWidths=[120, 60, 60])
                table.setStyle(TableStyle([('LINEAFTER', (0, 0), (-1, lign-1), 0.5, colors.black),
                                           ('LINEBEFORE', (0, 0), (-1, lign-1), 0.5, colors.black),
                                           ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
                                           ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.black)]))
                for idc in range(len(total_index)):
                    table.setStyle(TableStyle([
                        ('LINEBELOW', (0, total_index[idc]), (-1, total_index[idc]), 2, colors.black),
                        ('LINEABOVE', (0, total_index[idc]), (-1, total_index[idc]), 0.5, colors.black)
                    ]))
                total_index = []
                table.wrapOn(self.c, self.width, self.height)
                if first_page is True:
                    table.drawOn(self.c, 60, 105-lign)
                    nb_last_lign = 105 - lign
                    first_page = False
                else:
                    table.drawOn(self.c, 60, 250 - lign)
                    nb_last_lign = 250 - lign

                table = [[''] * colonnes for _ in range(lignes)]
                table[0][0] = Paragraph("<b>Mode</b>", center)
                table[0][1] = Paragraph("<b>Number</b>", center)
                table[0][2] = Paragraph("<b>Aver. Current [uA]</b>", center)
                table[0][3] = Paragraph("<b>Time [ms]</b>", center)
                table[0][4] = Paragraph("<b>Total Time [ms]</b>", center)
                table[0][5] = Paragraph("<b>Energy [uWh]</b>", center)
                table[0][6] = Paragraph("<b>Total Energy [uWh]</b>", center)
                lign = 1
                data_to_print = False
                self.c.showPage()


        if data_to_print is True:
            table = Table(table, colWidths=[120, 60, 60])
            table.setStyle(TableStyle([('LINEAFTER', (0, 0), (-1, lign - 1), 0.5, colors.black),
                                       ('LINEBEFORE', (0, 0), (-1, lign - 1), 0.5, colors.black),
                                       ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
                                       ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.black)]))
            for idc in range(len(total_index)):
                table.setStyle(TableStyle([
                    ('LINEBELOW', (0, total_index[idc]), (-1, total_index[idc]), 2, colors.black),
                    ('LINEABOVE', (0, total_index[idc]), (-1, total_index[idc]), 0.5, colors.black)
                ]))
            table.wrapOn(self.c, self.width, self.height)
            if first_page is True:
                table.drawOn(self.c, 60, 105 - lign)
                self.c.showPage()
                nb_last_lign = 0
            else:
                table.drawOn(self.c, 60, 250 - lign)
                nb_last_lign = 250 - lign

        return nb_last_lign

    # ------------------------------------------------------------------------------------------------------------------
    def create_third_section(self, nb):
        """
        Create the space for the estimation
        """
        right = ParagraphStyle(name="right", alignment=TA_RIGHT)
        left = ParagraphStyle(name="left", alignment=TA_LEFT)

        colonnes = 5
        lignes = 30

        table = [[''] * colonnes for _ in range(lignes)]

        table[0][3] = Paragraph("<b>Power Estimation</b>", left)
        table[1][3] = Paragraph("<b>Power Estimation (max)</b>", left)
        table[2][3] = Paragraph("<b>Lifetime Estimation</b>", left)
        table[3][3] = Paragraph("<b>Lifetime Estimation (min)</b>", left)
        if self.get_estimaion_value(0) > 1000:
            table[0][4] = Paragraph('<b>'+str(round(self.get_estimaion_value(0)/1000, 2))+' mWh</b>', right)
        else:
            table[0][4] = Paragraph('<b>' + str(round(self.get_estimaion_value(0), 2)) + ' uWh</b>', right)
        if self.get_estimaion_value(1) > 1000:
            table[1][4] = Paragraph(str(round(self.get_estimaion_value(1)/1000, 2)) + ' mWh', right)
        else:
            table[1][4] = Paragraph(str(round(self.get_estimaion_value(1), 2)) + ' uWh', right)
        table[2][4] = Paragraph('<b>' + str(self.get_estimaion_value(2)) + '</b>', right)
        table[3][4] = Paragraph(str(self.get_estimaion_value(3)), right)
        lign = 4
        table = Table(table, colWidths=[60, 60, 60, 180, 120])
        table.setStyle(TableStyle([('LINEAFTER', (3, 0), (-1, lign - 1), 0.5, colors.black),
                                   ('LINEBEFORE', (3, 0), (-1, lign - 1), 0.5, colors.black),
                                   ('LINEBELOW', (3, 0), (-1, lign - 1), 0.5, colors.black),
                                   ('LINEABOVE', (3, 0), (-1, 0), 0.5, colors.black)]))
        table.wrapOn(self.c, self.width, self.height)
        table.drawOn(self.c, 60, 250 - (nb+10))

# ----------------------------------------------------------------------
    def add_data_value(self, id_lig, id_col, nb):
        self.data_value[id_lig][id_col] = nb

    def get_data_value(self, id_lig, id_col):
        return self.data_value[id_lig][id_col]

    def add_spreading_factor(self, nb):
        self.spreading_factor = nb

    def get_spreading_factor(self):
        return self.spreading_factor

    def set_data_acc(self, value):
        if value is True:
            self.data_acc = 'Enabled'
        else:
            self.data_acc = 'Disabled'

    def get_data_acc(self):
        return self.data_acc

    def add_estimation_value(self, id, nb):
        self.estimation_value[id] = nb

    def get_estimaion_value(self, id):
        return self.estimation_value[id]

    def add_board_name(self, id, name):
        self.board_name[id] = name

    def get_board_name(self, id):
        return self.board_name[id]

    def get_idr(self):
        return self.idr

    def set_idr(self, nb):
        self.idr = nb

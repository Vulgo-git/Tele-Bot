import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Gera relatórios em PDF para consultas"""
    
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"✅ PDFGenerator inicializado: {output_dir}")
    
    def generate_cpf_report(self, person_data: Dict, query_value: str) -> str:
        """Gera um relatório PDF para consulta de CPF"""
        try:
            filename = f"relatorio_cpf_{query_value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Criar PDF
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Estilo customizado
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c5aa0'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold',
                borderColor=colors.HexColor('#e0e0e0'),
                borderWidth=0.5,
                borderPadding=5
            )
            
            # Título
            elements.append(Paragraph("📋 RELATÓRIO DE CONSULTA - CPF", title_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Informações do relatório
            info_data = [
                ['Data da Consulta:', datetime.now().strftime('%d/%m/%Y às %H:%M:%S')],
                ['Tipo de Consulta:', 'CPF'],
                ['Status:', '✅ Encontrado' if person_data else '❌ Não encontrado']
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.3*inch))
            
            if person_data:
                # Dados encontrados
                elements.append(Paragraph("📑 DADOS PESSOAIS", heading_style))
                
                # Montar dados para a tabela
                person_info = [
                    ['CPF:', person_data.get('cpf', 'N/A')],
                    ['Nome Completo:', person_data.get('full_name', 'N/A')],
                    ['Data de Nascimento:', person_data.get('birth_date', 'N/A')],
                    ['Mãe:', person_data.get('mother_name', 'N/A')],
                    ['Telefone:', person_data.get('phone', 'N/A')],
                    ['Email:', person_data.get('email', 'N/A')],
                ]
                
                person_table = Table(person_info, colWidths=[2*inch, 4*inch])
                person_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
                ]))
                elements.append(person_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # Endereço
                if person_data.get('address') or person_data.get('city'):
                    elements.append(Paragraph("📍 ENDEREÇO", heading_style))
                    
                    address_info = [
                        ['Endereço:', person_data.get('address', 'N/A')],
                        ['Cidade:', f"{person_data.get('city', 'N/A')} - {person_data.get('state', 'N/A')}"],
                        ['CEP:', person_data.get('zipcode', 'N/A')],
                    ]
                    
                    address_table = Table(address_info, colWidths=[2*inch, 4*inch])
                    address_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                        ('TOPPADDING', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                    ]))
                    elements.append(address_table)
            else:
                elements.append(Paragraph("❌ Nenhum resultado encontrado para esta consulta.", styles['Normal']))
            
            # Rodapé
            elements.append(Spacer(1, 0.5*inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(
                "Este relatório foi gerado automaticamente e é válido apenas para fins informativos.",
                footer_style
            ))
            
            # Construir PDF
            doc.build(elements)
            logger.info(f"✅ PDF gerado com sucesso: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF de CPF: {e}")
            return None
    
    def generate_phone_report(self, person_data: Dict, query_value: str) -> str:
        """Gera um relatório PDF para consulta de telefone"""
        try:
            filename = f"relatorio_telefone_{query_value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Criar PDF
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Estilo customizado
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c5aa0'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            )
            
            # Título
            elements.append(Paragraph("📱 RELATÓRIO DE CONSULTA - TELEFONE", title_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Informações do relatório
            info_data = [
                ['Data da Consulta:', datetime.now().strftime('%d/%m/%Y às %H:%M:%S')],
                ['Tipo de Consulta:', 'Telefone'],
                ['Telefone Consultado:', query_value],
                ['Status:', '✅ Encontrado' if person_data else '❌ Não encontrado']
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.3*inch))
            
            if person_data:
                # Dados encontrados
                elements.append(Paragraph("📑 INFORMAÇÕES DO TITULAR", heading_style))
                
                person_info = [
                    ['Nome Completo:', person_data.get('full_name', 'N/A')],
                    ['CPF:', person_data.get('cpf', 'N/A')],
                    ['Telefone:', person_data.get('phone', 'N/A')],
                    ['Email:', person_data.get('email', 'N/A')],
                    ['Data de Nascimento:', person_data.get('birth_date', 'N/A')],
                ]
                
                person_table = Table(person_info, colWidths=[2*inch, 4*inch])
                person_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
                ]))
                elements.append(person_table)
            else:
                elements.append(Paragraph("❌ Nenhum resultado encontrado para este telefone.", styles['Normal']))
            
            # Rodapé
            elements.append(Spacer(1, 0.5*inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(
                "Este relatório foi gerado automaticamente e é válido apenas para fins informativos.",
                footer_style
            ))
            
            # Construir PDF
            doc.build(elements)
            logger.info(f"✅ PDF gerado com sucesso: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF de telefone: {e}")
            return None
    
    def generate_name_report(self, persons_data: List[Dict], query_value: str) -> str:
        """Gera um relatório PDF para consulta por nome"""
        try:
            filename = f"relatorio_nome_{query_value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Criar PDF
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Estilo customizado
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            # Título
            elements.append(Paragraph("👤 RELATÓRIO DE CONSULTA - NOME", title_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Informações do relatório
            info_data = [
                ['Data da Consulta:', datetime.now().strftime('%d/%m/%Y às %H:%M:%S')],
                ['Tipo de Consulta:', 'Nome'],
                ['Nome Consultado:', query_value],
                ['Resultados Encontrados:', str(len(persons_data))]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.3*inch))
            
            if persons_data:
                # Tabela com resultados
                table_data = [['Nome Completo', 'CPF', 'Telefone', 'Data Nasc.']]
                
                for person in persons_data:
                    table_data.append([
                        person.get('full_name', 'N/A'),
                        person.get('cpf', 'N/A'),
                        person.get('phone', 'N/A'),
                        person.get('birth_date', 'N/A'),
                    ])
                
                results_table = Table(table_data, colWidths=[2.2*inch, 1.3*inch, 1.3*inch, 1.2*inch])
                results_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                    ('TOPPADDING', (0, 1), (-1, -1), 8),
                ]))
                elements.append(results_table)
            else:
                elements.append(Paragraph("❌ Nenhum resultado encontrado para este nome.", styles['Normal']))
            
            # Rodapé
            elements.append(Spacer(1, 0.5*inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(
                "Este relatório foi gerado automaticamente e é válido apenas para fins informativos.",
                footer_style
            ))
            
            # Construir PDF
            doc.build(elements)
            logger.info(f"✅ PDF gerado com sucesso: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF de nome: {e}")
            return None

import io
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- CAMINHO ABSOLUTO E ROBUSTO PARA A RAIZ DO PROJETO ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Funções de Desenho ---

def draw_watermark(canvas_obj, width, height):
    """Desenha a logo grande como marca d'água semi-transparente."""
    canvas_obj.saveState()
    watermark_path = os.path.join(PROJECT_ROOT, 'frontend', 'static', 'img', 'logo_santaisabel (longo).png')
    
    if os.path.exists(watermark_path):
        img_width = 4 * inch
        x = (width - img_width) / 2
        y = (height - (img_width * 0.5)) / 2
        canvas_obj.setFillAlpha(0.25)
        canvas_obj.drawImage(watermark_path, x, y, width=img_width, preserveAspectRatio=True, mask='auto')
        
    canvas_obj.restoreState()

def draw_header(canvas_obj, width):
    """Desenha o cabeçalho de forma estruturada e alinhada."""
    canvas_obj.saveState()
    logo_path = os.path.join(PROJECT_ROOT, 'frontend', 'static', 'img', 'logo_santaisabel.png')

    # --- LÓGICA DE ALINHAMENTO CORRIGIDA ---
    
    # Linha horizontal de referência
    line_y = letter[1] - 1.3 * inch
    
    # 1. Desenha a logo BEM NO LIMITE da margem esquerda
    logo_height = 0.7 * inch
    logo_width_default = 0.7 * inch 
    logo_x = 0.5 * inch  # Bem no limite esquerdo
    logo_y_draw = line_y + 0.05 * inch  # Um pouco acima da linha
    
    logo_width_real = logo_width_default
    if os.path.exists(logo_path):
        try:
            img_info = canvas_obj.drawImage(logo_path, logo_x, logo_y_draw, 
                                            height=logo_height, 
                                            preserveAspectRatio=True, 
                                            mask='auto')
            logo_width_real = img_info[0]
        except Exception as e:
            print(f"Aviso: Nao foi possivel desenhar a logo: {e}")
    else:
        print(f"Aviso: Arquivo da logo nao encontrado em: {logo_path}")

    # 2. Texto "Município de Santa Isabel" 
    text_x_pos = logo_x + logo_width_real + 3  # Apenas 3 pontos de espaço (bem coladinho)
    text_y_pos = logo_y_draw + (logo_height / 2) - 0.05 * inch  # Centralizado com a logo
    
    canvas_obj.setFont('Helvetica', 10)
    canvas_obj.drawString(text_x_pos, text_y_pos, "Município de Santa Isabel")

    
    # 4. Linha horizontal
    canvas_obj.setStrokeColorRGB(0.8, 0.8, 0.8)
    canvas_obj.line(0.5 * inch, line_y, width - 0.5 * inch, line_y)
    
    canvas_obj.restoreState()

def draw_footer(canvas_obj, width):
    """Desenha o rodapé."""
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setStrokeColorRGB(0.8, 0.8, 0.8)
    canvas_obj.line(inch, 0.75 * inch, width - inch, 0.75 * inch)
    canvas_obj.drawString(inch, 0.5 * inch, "Sistema de Controle de Casos - D.T.I.")
    generation_date = datetime.now().strftime("Gerado em %d/%m/%Y às %H:%M:%S")
    canvas_obj.drawCentredString(width / 2, 0.5 * inch, generation_date)
    page_num_text = f"Página {canvas_obj.getPageNumber()}"
    canvas_obj.drawRightString(width - inch, 0.5 * inch, page_num_text)
    canvas_obj.restoreState()

def generate_case_pdf(caso):
    """Gera um relatório PDF profissional para um caso específico."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # --- Ordem de Desenho ---
    # 2. Desenha o cabeçalho (topo)
    draw_header(p, width)
    
    # 3. Desenha o rodapé (base)
    draw_footer(p, width)
    
    # 4. Começa a desenhar o conteúdo principal (entre cabeçalho e rodapé)
    y_position = height - 2 * inch # Posição inicial abaixo da linha do cabeçalho
    
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawString(inch, y_position, "Detalhes Gerais do Caso")
    
    y_position -= 30
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.black)
    
    details = {
        "Status do Caso": caso.status.upper(),
        "Última Atualização": caso.ultima_atualizacao.strftime('%d/%m/%Y %H:%M:%S'),
        "Nome do Solicitante": caso.nome_solicitante,
        "Nº Patrimônio": caso.numero_patrimonio or 'N/A',
        "Ramal": caso.ramal or 'N/A',
        "Secretaria": caso.secretaria or 'N/A',
        "Departamento": caso.departamento or 'N/A',
    }
    
    for key, value in details.items():
        # Adiciona verificação para não desenhar fora da página
        if y_position < 1.5 * inch:
            p.showPage()
            
            draw_header(p, width)
            draw_footer(p, width)
            y_position = height - 1.7 * inch # Reinicia no topo (abaixo do header)
            
        p.setFont("Helvetica-Bold", 10)
        p.drawString(inch, y_position, f"{key}:")
        p.setFont("Helvetica", 10)
        p.drawString(inch * 2.5, y_position, value)
        y_position -= 20
        
    y_position -= 20 # Espaço extra
    
    # --- Descrição do Problema (com quebra de linha) ---
    if y_position < 2.5 * inch: # Checa espaço para o título + algum texto
         p.showPage()
         
         draw_header(p, width)
         draw_footer(p, width)
         y_position = height - 1.7 * inch
         
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawString(inch, y_position, "Descrição do Problema")
    y_position -= 30
    
    text_object = p.beginText(inch, y_position)
    text_object.setFont("Helvetica", 10)
    text_object.setLeading(14)
    
    problem_text = caso.problema_descricao or 'Nenhuma descrição fornecida.'
    
    # Lógica simples de quebra de página para texto longo
    for line in problem_text.split('\n'):
        if text_object.getY() < 1.5 * inch:
            p.drawText(text_object) # Desenha o que tem
            p.showPage()
            
            draw_header(p, width)
            draw_footer(p, width)
            y_position = height - 1.7 * inch
            text_object = p.beginText(inch, y_position) # Começa novo text object
            text_object.setFont("Helvetica", 10)
            text_object.setLeading(14)
            
        text_object.textLine(line)
        
    p.drawText(text_object)
    y_position = text_object.getY() - 20 # Pega a última posição Y do texto
    
    # --- Solução Aplicada (com quebra de linha) ---
    if y_position < 2.5 * inch: # Checa espaço para o título + algum texto
         p.showPage()
         
         draw_header(p, width)
         draw_footer(p, width)
         y_position = height - 1.7 * inch

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.black)
    p.drawString(inch, y_position, "Solução Aplicada")
    y_position -= 30

    solution_text_object = p.beginText(inch, y_position)
    solution_text_object.setFont("Helvetica", 10)
    solution_text_object.setLeading(14)
    
    solution_text = caso.solucao_descricao or 'Nenhuma solução fornecida.'
    
    for line in solution_text.split('\n'):
        if solution_text_object.getY() < 1.5 * inch:
            p.drawText(solution_text_object) # Desenha o que tem
            p.showPage()
            
            draw_header(p, width)
            draw_footer(p, width)
            y_position = height - 1.7 * inch
            solution_text_object = p.beginText(inch, y_position) # Começa novo text object
            solution_text_object.setFont("Helvetica", 10)
            solution_text_object.setLeading(14)

        solution_text_object.textLine(line)
        
    p.drawText(solution_text_object)
    
    # --- Finalização ---
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

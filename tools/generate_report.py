from datetime import date
from pathlib import Path
import re
import subprocess
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs"
EVIDENCE_DIR = OUTPUT_DIR / "evidencias"
REPORT_PATH = OUTPUT_DIR / "relatorio_tecnico.pdf"
EVIDENCE_PATH = EVIDENCE_DIR / "execucao_pytest.txt"


def run_tests() -> str:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--cov=src",
        "--cov-report=term-missing",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = f"$ {' '.join(command)}\n\n{result.stdout}"
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(output, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"A execução dos testes falhou. Consulte {EVIDENCE_PATH}")
    return result.stdout


def make_report(test_output: str) -> None:
    total_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", test_output)
    passed_match = re.search(r"(\d+) passed(?:,\s+(\d+) warnings?)?", test_output)
    coverage = total_match.group(1) if total_match else "não identificado"
    passed = passed_match.group(1) if passed_match else "não identificado"
    warnings = passed_match.group(2) if passed_match and passed_match.group(2) else "0"

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17324D"),
            spaceAfter=8 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#176B68"),
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
            spaceAfter=2 * mm,
        )
    )

    document = SimpleDocTemplate(
        str(REPORT_PATH),
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=17 * mm,
        bottomMargin=17 * mm,
        title="Relatório Técnico - Testes de Integração AeroLog",
        author="Projeto acadêmico de Qualidade e Teste de Software",
    )
    story = [
        Paragraph("Relatório Técnico", styles["ReportTitle"]),
        Paragraph(
            "Testes de Integração: Sistema de Agendamento e Controle de Voos de Helicóptero",
            styles["Heading1"],
        ),
        Paragraph("AeroLog Helicópteros | Qualidade e Teste de Software", styles["BodyText"]),
        Paragraph(f"Execução registrada em {date.today().strftime('%d/%m/%Y')}", styles["BodyText"]),
        Spacer(1, 4 * mm),
        Paragraph("1. Introdução e contextualização", styles["Section"]),
        Paragraph(
            "O sistema avaliado agenda voos de táxi aéreo e transporte offshore. Uma falha ao "
            "permitir aeronave em inspeção, exceder capacidade ou reservar uma aeronave já "
            "ocupada pode comprometer a operação. Os testes exercitam conjuntamente o serviço, "
            "as regras de elegibilidade e o SQLite, sem API HTTP.",
            styles["SmallBody"],
        ),
        Paragraph("2. Arquitetura e integrações", styles["Section"]),
        Paragraph(
            "O BookingService abre uma transação SQLite com BEGIN IMMEDIATE, carrega a aeronave, "
            "chama FlightValidator, verifica sobreposição de intervalos e insere o agendamento "
            "com status AGENDADO. Exceções abortam a transação; chaves estrangeiras e restrições "
            "do banco também protegem a integridade dos registros.",
            styles["SmallBody"],
        ),
        Preformatted(
            "BookingService\n    |-- FlightValidator (manutenção e capacidade)\n"
            "    |-- Database / SQLite (aeronaves, pilotos, agendamentos)\n"
            "    `-- rollback automático em falha",
            ParagraphStyle("Diagram", fontName="Courier", fontSize=8, leading=11),
        ),
        Paragraph("3. Matriz de cenários de teste", styles["Section"]),
    ]

    rows = [
        ["Cenário", "Entrada e ação", "Esperado e obtido"],
        ["1. Caminho feliz", "Aeronave LIBERADO, 760 kg, intervalo livre.", "Aprovado; registro persistido como AGENDADO."],
        ["2. Conflito", "Segundo voo sobreposto para a mesma aeronave.", "BookingConflict; segundo registro não inserido."],
        ["3. Manutenção", "Aeronave EM_INSPECAO.", "ValidationError; banco permanece sem agendamento."],
        ["4. Isolamento", "Fixture tmp_path cria SQLite por teste.", "Cada teste inicia sem registros de testes anteriores."],
        ["Adicional. Peso", "Peso informado acima da carga útil.", "ValidationError; nenhuma gravação realizada."],
    ]
    matrix = Table(rows, colWidths=[27 * mm, 65 * mm, 71 * mm], repeatRows=1)
    matrix.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#A9B8C5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F5F5")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend(
        [
            matrix,
            Paragraph("4. Evidências de execução e cobertura", styles["Section"]),
            Paragraph(
                f"A execução capturada registrou {passed} testes aprovados e {warnings} avisos. "
                f"A cobertura total dos módulos em src/ foi de {coverage}%. A saída integral "
                f"do pytest está em docs/evidencias/execucao_pytest.txt; ela é uma transcrição "
                "direta do processo de teste, não uma captura de tela do terminal.",
                styles["SmallBody"],
            ),
            Preformatted(
                "Resumo real da execução:\n" + "\n".join(
                    line for line in test_output.splitlines()
                    if "PASSED" in line or "TOTAL" in line or "passed in" in line
                ),
                ParagraphStyle("Evidence", fontName="Courier", fontSize=7, leading=9),
            ),
            Paragraph("5. Conclusão e lições aprendidas", styles["Section"]),
            Paragraph(
                "A fixture baseada em tmp_path mantém cada teste isolado e dispensa limpeza "
                "manual de uma base compartilhada. A transação mantém a consistência entre "
                "validação e persistência; BEGIN IMMEDIATE serializa escritores concorrentes, "
                "reduzindo a janela para reservas simultâneas da mesma aeronave. A suíte confirmou "
                "os cinco comportamentos cobertos nesta execução. A cobertura é uma métrica de "
                "execução de linhas, não uma prova isolada de ausência de defeitos.",
                styles["SmallBody"],
            ),
        ]
    )
    document.build(story)


if __name__ == "__main__":
    output = run_tests()
    make_report(output)
    print(f"Relatório gerado: {REPORT_PATH.relative_to(ROOT)}")
    print(f"Evidência gerada: {EVIDENCE_PATH.relative_to(ROOT)}")
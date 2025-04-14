"""
Task definitions for the PDF Search project.
"""
import datetime
from textwrap import dedent
from crewai import Task
from config.settings import OUTPUT_DIR
import os

def create_task(
    description,
    expected_output,
    agent,
    context=None,
    output_prefix="output"
):
    """
    Create a task with the specified parameters.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"{output_prefix}_{timestamp}.md")

    return Task(
        description=dedent(description),
        expected_output=dedent(expected_output),
        agent=agent,
        context=context,
        output_file=output_file
    )

def create_tasks(var_1, var_2, var_3, agents):
    """
    Create a set of tasks with the specified variables and agents.
    """
    agent_1, agent_2, agent_3, agent_metadata = agents

    # Task 0: Metadata extraction (Arabic)
    task_0 = create_task(
        description="""
        استخرج البيانات الأساسية من وثيقة PDF باللغة العربية:
        - الرقم الداخلي
        - التاريخ
        - المرسل إليه
        - الموضوع

        يجب تنسيق الناتج على شكل قائمة باللغة العربية.
        """,
        expected_output="""
        قائمة منظمة تحتوي على:
        1. الرقم الداخلي
        2. التاريخ
        3. المرسل إليه
        4. الموضوع
        """,
        agent=agent_metadata,
        output_prefix="metadata"
    )

    # Task 1: Initial PDF analysis
    task_1 = create_task(
        description=f"""
        Analyze the provided PDF document to identify and extract key information.
        ---
        TOPIC: "{var_1}"
        FOCUS AREA: "{var_2}"
        DESIRED DETAIL LEVEL: "{var_3}"

        Use the PDFSearchTool to search for relevant content in the PDF.
        Provide a comprehensive analysis of the key concepts, methodologies, and findings
        related to the topic and focus area specified above.
        """,
        expected_output="""
        A detailed analysis of the PDF content, including:
        1. Overview of key concepts identified
        2. Summary of methodologies described
        3. Explanation of important findings or results
        4. List of technical terms and their definitions

        The analysis should be well-structured with clear sections and subsections.
        """,
        agent=agent_1,
        context=[task_0],
        output_prefix="analysis"
    )

    # Task 2: Knowledge structuring
    task_2 = create_task(
        description=f"""
        Based on the previous analysis, create a structured knowledge representation
        of the information found in the PDF.
        ---
        TOPIC: "{var_1}"
        FOCUS AREA: "{var_2}"
        DESIRED DETAIL LEVEL: "{var_3}"

        Use the PDFSearchTool for additional details as needed. Organize the information
        into logical categories, establish relationships between concepts, and create
        a cohesive knowledge structure.
        """,
        expected_output="""
        A structured knowledge representation, including:
        1. Hierarchical organization of concepts
        2. Concept map or relationship diagram (described in text)
        3. Categorization of information by themes or domains
        4. Identification of gaps or areas for further investigation

        The output should emphasize clarity and logical organization.
        """,
        agent=agent_2,
        context=[task_1],
        output_prefix="knowledge_structure"
    )

    # Task 3: Final report generation
    task_3 = create_task(
        description=f"""
        Create a comprehensive final report based on the previous analysis and
        knowledge structuring.
        ---
        TOPIC: "{var_1}"
        FOCUS AREA: "{var_2}"
        DESIRED DETAIL LEVEL: "{var_3}"

        Use the PDFSearchTool to verify and add any missing information. The report
        should synthesize all findings into a cohesive document that provides valuable
        insights and conclusions.
        """,
        expected_output="""
        A comprehensive final report, including:
        1. Executive summary
        2. Detailed findings with supporting evidence
        3. Visual representations of key concepts (described in text)
        4. Conclusions and implications
        5. Recommendations for further exploration or application

        The report should be polished, professional, and ready for presentation.
        """,
        agent=agent_3,
        context=[task_2],
        output_prefix="final_report"
    )

    return [task_0, task_1, task_2, task_3]

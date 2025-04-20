from crewai import Task
from textwrap import dedent

class EmailFilterTasks:
    def filter_emails_task(self, agent, emails):
        return Task(
            description=dedent(f"""\
                Analyze a batch of emails and filter out
                non-essential ones such as newsletters, promotional content and notifications.

                Use your expertise in email content analysis to distinguish
                important emails from the rest, pay attention to the sender and avoid invalid emails.

                Make sure to filter for the messages actually directed at the user and avoid notifications.

                EMAILS
                -------
                {emails}

                Your final answer MUST be the relevant thread_ids and the sender, use bullet points.
            """),
            expected_output="A list of relevant thread IDs and senders in bullet point format.",
            agent=agent
        )

    def action_required_emails_task(self, agent):
        return Task(
            description=dedent("""\
                For each email thread, fetch and analyze the complete thread using only the actual Thread ID.
                Understand the context, key points, and the overall sentiment of the conversation.

                Identify the main query or concerns that needs to be addressed in the response for each.

                Your final answer MUST be a list for all emails with:
                - the thread_id
                - a summary of the email thread
                - a highlighting with the main points
                - identify the user and who he will be answering to
                - communication style in the thread
                - the sender's email address
                - a list of attachments (if any)
                - a summary of each attachment's content (if possible)
                - a review of any links found (if possible)
            """),
            expected_output="A detailed analysis of each email thread with thread ID, summary, main points, communication style, and attachment information.",
            agent=agent
        )
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
                For each email thread, analyze the complete thread.
                Your final answer MUST use this EXACT format for each email:

                ### Thread ID: [thread_id]
                **Subject:** [subject]
                **Sender's Email Address:** [sender_email]
                **Summary:** [thread_summary]
                **Main Points:**
                - [point 1]
                - [point 2]
                **Attachments:** [filename1, filename2] or None
                """),
            expected_output="A detailed analysis of each email thread in the specified format.",
            agent=agent
        )
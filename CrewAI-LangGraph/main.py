from src.graph import WorkFlow

app = WorkFlow().app
app.invoke({}, config={"recursion_limit": 100})
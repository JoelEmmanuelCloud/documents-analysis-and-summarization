def get_system_prompt():
    system_prompt = """
You are an office assistant working on analyzing and summarizing the content of a file.
"""
    return system_prompt


def get_user_prompt():

    json_response_format = """
{
    "Title": "",
    "Summary": ""
}
"""
    user_prompt = f"""
Your task is to summarize the information from the document and provide both a title and a summary for the text content.

Take a deep breath and carefully review your response. Make sure to check the JSON formatting and information multiple times to ensure there are no errors. Your response is crucial to the process, so pay close attention to the accuracy of the JSON formatting.

The response format should follow:
{json_response_format}
"""
    return user_prompt

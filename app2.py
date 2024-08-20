import streamlit as st
from tavily import TavilyClient
from openai import OpenAI
import os

st.set_page_config(page_title="brain bytes", layout="wide")

# Initialize Tavily and Ollama (make sure to configure your API keys if needed)
tavily_client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])
openai_client = OpenAI(api_key=st.secrets["openai"]["api_key"])


FILES_DIR = './files'
os.makedirs(FILES_DIR, exist_ok=True)

def create_download_content(content, filename):
    file_path = os.path.join(FILES_DIR, filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    return file_path

def scrape_web(query):
    # Use Tavily to scrape the internet based on the user's query
    search_results = tavily_client.search(query=query)
    return search_results

def summarize_with_openai(text, level):
    # Adjust the prompt based on the selected level
    level_prompts = {
        'very young child': (
            "please summarize the following information in a way that a very young child can understand. "
            "use very simple words, short sentences, and lots of fun. include playful language and make it "
            "engaging with simple examples or illustrations if possible."
        ),
        'young child': (
            "please summarize the following information in a way that a young child can understand. "
            "use simple words and short sentences. make it interesting and fun, with easy examples or stories "
            "to help explain the main points."
        ),
        'older child': (
            "please summarize the following information in a way that an older child can understand. "
            "use clear and straightforward language, with some detail. make it engaging and include some fun "
            "facts or relatable examples to help clarify the main ideas."
        ),
        'teenager': (
            "please summarize the following information in a way that a teenager can understand. "
            "use detailed explanations and slightly advanced language. include relevant examples, analogies, or "
            "current trends to make the information engaging and relatable."
        ),
        'adult': (
            "please summarize the following information in a way that an adult can understand. "
            "provide a thorough explanation with appropriate depth and complexity. use formal language and include "
            "relevant data, examples, or references to ensure the summary is comprehensive and informative."
        )
    }

    prompt = level_prompts.get(level, level_prompts['very young child'])  # Default to 'very young child' if level not found
    prompt += f"""\n\n
                Instruction: Put the summary in a markdown format with headings, subheadings, and bullet points.
                If the summary includes the code block markers, remove them.
            
                Text to summarize:
                {text}
            """

    try:
        response = openai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )

        # Extract and return the content from the response
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while summarizing the text."

def get_markdown_files(folder_path):
    # List all files in the directory
    all_files = os.listdir(folder_path)
    
    # Filter for Markdown files
    markdown_files = [f for f in all_files if f.endswith('.md')]
    
    return markdown_files

def read_file_content(file_path):
    with open(file_path, 'r') as file:
        return file.read()
    
def page_file_viewer():
    st.title("previous discoveries")
    
    markdown_files = get_markdown_files(FILES_DIR)
    if markdown_files:
        selected_file = st.selectbox("select a file to view:", markdown_files)
        if selected_file:
            file_path = os.path.join(FILES_DIR, selected_file)
            file_content = read_file_content(file_path)
            st.markdown(file_content)
    else:
        st.write("no files available.")

def page_search_summary():
    st.title("discover something new")
    
    # Input query from the user
    query = st.text_input("enter your search query:")

    # Dropdown to select the level of explanation
    level = st.selectbox(
        "select the level of explanation:",
        ["very young child", "young child", "older child", "teenager", "adult"]
    )

    # Button to start the search
    if st.button("look up"):
        if query:
            with st.spinner("scraping the web for information..."):
                search_results = scrape_web(query)

            if search_results and 'results' in search_results:
                # Combine all results into a single string
                combined_results = "\n\n".join(result['content'] for result in search_results['results'])

                # Summarize the information based on the selected level
                with st.spinner("summarizing the information..."):
                    summarized_text = summarize_with_openai(combined_results, level)

                # Display the summarized information in markdown format
                st.markdown(summarized_text)

                # Save the summarized text to a file
                filename = f"{query.lower().replace(' ', '_')}.md"
                create_download_content(summarized_text, filename)
                
                # Provide a download button
                st.download_button(
                    label="download summary",
                    data=summarized_text,
                    file_name=filename,
                    mime="text/markdown"
                )
            else:
                st.warning("no results found. please try a different query.")
        else:
            st.warning("please enter a search query.")

def main():
    st.sidebar.title("brain bytes")
    page = st.sidebar.radio("pages", ["discover something new", "previous discoveries"])

    if page == "discover something new":
        page_search_summary()
    elif page == "previous discoveries":
        page_file_viewer()

if __name__ == "__main__":
    main()

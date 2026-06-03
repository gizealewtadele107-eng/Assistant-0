import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import gradio as gr

def run_wikipedia_search(search_keyword):
    if not search_keyword:
        return "⚠️ እባክዎ መጀመሪያ የሚፈለግ ቃል ያስገቡ!"

    # 1. ክሮም ብሮውዘር በጀርባ (Headless) እንዲሠራ ማዘጋጀት
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # በRender ላይ ክሮም ያለበትን ቦታ ማሳወቅ (ለBuildpack አስገዳጅ ነው)
    chrome_options.binary_location = "/app/.apt/usr/bin/google-chrome"
    
    print("🤖 ብሮውዘሩ በጀርባ እየተከፈተ ነው...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 2. ወደ ዊኪፒዲያ ድረ-ገጽ መሄድ
        driver.get("https://www.wikipedia.org/")
        time.sleep(3)
        
        # 3. [ጽሑፍ መጻፍ] - የፍለጋ ሳጥኑን (Search Input) በ ID ፈልጎ ማግኘት
        search_box = driver.find_element(By.ID, "searchInput")
        
        # 4. ሳጥኑ ውስጥ ቃሉን መተየብ
        search_box.send_keys(search_keyword)
        print(f"✍️ '{search_keyword}' የሚለው ቃል ተጽፏል...")
        time.sleep(1)
        
        # 5. [በተን መጫን] - የፍለጋ በተኑን (Search Button) በ CSS Selector ፈልጎ መጫን
        search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        print("🎯 የፍለጋ በተኑ ተጭኗል!")
        time.sleep(4)
        
        # 6. ውጤት - ቦቱ በተኑን ተጭኖ የደረሰበትን አዲስ ገጽ አርዕስት (Title) ማንበብ
        page_title = driver.title
        current_url = driver.current_url
        
        return f"🟢 ቦቱ በተኑን በተሳካ ሁኔታ ተጭኗል!\n📌 የደረሰበት ገጽ አርዕስት፦ {page_title}\n🌐 ሊንክ፦ {current_url}"
        
    except Exception as e:
        return f"❌ ስህተት አጋጥሟል፦ {str(e)}"
    finally:
        # 7. ብሮውዘሩን መዝጋት
        driver.quit()

# --- የGradio በይነገጽ (UI) ---
with gr.Blocks() as demo:
    gr.Markdown("# 🧪 የዌብ አውቶሜሽን (Click & Type) መማሪያ")
    gr.Markdown("ይህ ቦት በሰርቨር ላይ ሆኖ በተን መጫን እና ጽሑፍ መጻፍ እንዴት እንደሚቻል ያሳያል።")
    
    user_input = gr.Textbox(label="የሚፈለግ ቃል ያስገቡ (ምሳሌ፡ Ethiopia)፦", placeholder="እዚህ ይጻፉ...")
    btn = gr.Button("🚀 ቦቱን በጀርባ አዝዘው", variant="primary")
    output_text = gr.Textbox(label="የቦቱ የሥራ ሂደት ውጤት፦")
    
    btn.click(run_wikipedia_search, inputs=user_input, outputs=output_text)

if __name__ == '__main__':
    render_port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=render_port)

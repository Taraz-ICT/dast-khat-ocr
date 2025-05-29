import requests
import base64
import re
import sys
import os
from PIL import Image
import time

API_KEY = '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'
API_URL = 'https://openrouter.ai/api/v1/chat/completions'
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

def persian_ocr_scanner(image_path):
    """Extract Persian text from an image using OCR"""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        img.thumbnail((1024, 1024))
        
        from io import BytesIO
        byte_arr = BytesIO()
        img.save(byte_arr, format='JPEG', quality=85)
        base64_image = base64.b64encode(byte_arr.getvalue()).decode("utf-8")
        
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return None
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    persian_prompt = """
    تمام متن فارسی موجود در تصویر را دقیقاً به همان شکل استخراج کن. موارد زیر را رعایت کن:
    ۱. متن را دقیقاً با همان خط و فاصله‌ها بنویس
    ۲. حروف و اعداد فارسی را کاملاً حفظ کن
    ۳. جهت نوشتار راست به چپ را حفظ کن
    ۴. علائم نگارشی و اعداد عربی را تغییر نده
    ۵. اگر متن انگلیسی هم وجود دارد، آن را جداگانه مشخص کن
    """
    
    data = {
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": persian_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(API_URL, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        persian_text = result['choices'][0]['message']['content']
        
        cleaned_text = re.sub(r'^.*?(?=[\u0600-\u06FF])', '', persian_text, flags=re.DOTALL)
        cleaned_text = re.sub(r'[\u200c\u200d]', '', cleaned_text)
        
        return cleaned_text.strip()
    
    except Exception as e:
        print(f"API error for {image_path}: {str(e)}")
        return None

def process_image_folder(folder_path):
    """Process all images in a folder and save OCR results"""
    output_dir = os.path.join(folder_path, "ocr_results")
    os.makedirs(output_dir, exist_ok=True)
    
    image_files = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and 
        f.lower().endswith(SUPPORTED_EXTENSIONS)
    ]
    
    if not image_files:
        print("No supported images found in folder.")
        return
    
    print(f"Found {len(image_files)} images to process...")
    
    for i, filename in enumerate(image_files):
        image_path = os.path.join(folder_path, filename)
        print(f"\n{'='*50}")
        print(f"Processing {i+1}/{len(image_files)}: {filename}")
        print(f"{'='*50}")
        
        start_time = time.time()
        extracted_text = persian_ocr_scanner(image_path)
        process_time = time.time() - start_time
        
        if extracted_text:
            # Save to text file
            output_filename = os.path.splitext(filename)[0] + ".txt"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            # Display preview of extracted text
            print("\nOCR Successful!")
            print(f"Processing time: {process_time:.1f} seconds")
            print(f"Character count: {len(extracted_text)}")
            print(f"Saved to: {output_path}")
            
            print("\nText Preview (first 10 lines):")
            print("-"*50)
            # Show first 10 lines of text
            lines = extracted_text.splitlines()[:10]
            for j, line in enumerate(lines):
                print(f"{j+1}: {line}")
            print("-"*50)
            print(f"Showing {min(10, len(lines))} of {len(extracted_text.splitlines())} lines")
        else:
            print(f"\nFailed to process {filename}")

# Terminal encoding setup
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

if __name__ == "__main__":
    print("Persian OCR Batch Processor")
    print("="*50)
    print("Note: the results kept in specified folder")
    
    folder_path = input("Enter folder path with images (or press Enter for current directory): ").strip()
    
    if not folder_path:
        folder_path = os.getcwd()
    
    if not os.path.isdir(folder_path):
        print(f"\nError: '{folder_path}' is not a valid directory")
    else:
        print(f"\nStarting Persian OCR processing for: {folder_path}")
        start_total = time.time()
        process_image_folder(folder_path)
        total_time = time.time() - start_total
        print(f"\n{'='*50}")
        print(f"Processing complete! Total time: {total_time/60:.1f} minutes")
        print(f"Results saved to: {os.path.join(folder_path, 'ocr_results')}")
        print("="*50)
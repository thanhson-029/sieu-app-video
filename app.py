from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import google.generativeai as genai
import time
import os
import shutil
import csv

app = FastAPI()

# ANH DÁN LẠI API KEY GOOGLE CỦA ANH VÀO ĐÂY NHÉ
GEMINI_API_KEY = "AIzaSyCto0MS5p4ZDF_5QG5gE4DeNZ0ao9ZWoYk" 

genai.configure(api_key=GEMINI_API_KEY)

# =====================================================================
# 1. GIAO DIỆN WEB FRONTEND (SAAS DASHBOARD PROTOTYPE)
# =====================================================================
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Siêu App AI Video Shorts - SaaS Node</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body class="bg-slate-900 text-slate-100 font-sans min-h-screen">

        <header class="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
            <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="bg-indigo-600 p-2 rounded-lg text-white font-bold">
                        <i class="fa-solid fa-wand-magic-sparkles text-lg"></i>
                    </div>
                    <span class="text-xl font-extrabold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                        Sieu Video AI
                    </span>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="hidden sm:flex flex-col text-right">
                        <span class="text-sm font-semibold text-slate-300">Thầy Sơn (Admin)</span>
                        <span class="text-xs text-emerald-400 font-medium"><i class="fa-solid fa-crown mr-1"></i>Gói SaaS Premium</span>
                    </div>
                    <div class="bg-slate-800 px-3 py-1.5 rounded-full text-xs font-mono text-cyan-400 border border-slate-700">
                        Credits: Vô hạn
                    </div>
                </div>
            </div>
        </header>

        <main class="max-w-4xl mx-auto px-4 py-10">
            
            <div class="text-center mb-10">
                <h1 class="text-3xl font-black tracking-tight mb-2 sm:text-4xl">
                    Tẩy Trắng Video Đối Thủ Thành <span class="text-indigo-400">Shorts Triệu View</span>
                </h1>
                <p class="text-slate-400 text-sm sm:text-base max-w-xl mx-auto">
                    Hệ thống tự động phân tích bối cảnh, cố định tạo hình nhân vật, khóa chuẩn 5 cảnh và xuất file kịch bản kèm Excel lồng tiếng chuyên nghiệp.
                </p>
            </div>

            <section class="bg-slate-850 border border-slate-800 rounded-2xl p-6 shadow-xl mb-8 bg-slate-800/30">
                <form id="uploadForm" class="space-y-6">
                    <div class="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-8 text-center cursor-pointer transition relative group" id="dropZone">
                        <input type="file" id="videoFile" accept="video/*" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" required>
                        <div class="space-y-3">
                            <div class="text-slate-400 group-hover:text-indigo-400 transition transform group-hover:-translate-y-1">
                                <i class="fa-solid fa-cloud-arrow-up text-4xl"></i>
                            </div>
                            <div class="text-sm font-medium text-slate-200" id="fileStatus">
                                Kéo thả video gốc vào đây hoặc <span class="text-indigo-400 underline">Chọn từ máy tính</span>
                            </div>
                            <div class="text-xs text-slate-500">Hỗ trợ định dạng MP4, MOV, AVI... dung lượng tối ưu</div>
                        </div>
                    </div>

                    <button type="submit" id="btnSubmit" class="w-full bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold py-3.5 px-4 rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center justify-center space-x-2 text-base">
                        <i class="fa-solid fa-bolt"></i>
                        <span>Bắt Đầu Phân Tích & Remake Video</span>
                    </button>
                </form>
            </section>

            <section id="loadingSection" class="hidden text-center py-12 bg-slate-800/20 rounded-2xl border border-slate-800/50 space-y-4">
                <div class="inline-block animate-spin text-indigo-500 text-4xl">
                    <i class="fa-solid fa-circle-notch"></i>
                </div>
                <div class="text-indigo-400 font-bold tracking-wider text-sm animate-pulse" id="loadingText">
                    ĐANG TẢI VIDEO LÊN GOOGLE AI STUDIO...
                </div>
                <p class="text-xs text-slate-500 max-w-xs mx-auto">Bộ não Gemini 2.5 Flash đang nghe lời thoại và bóc tách cấu trúc hình ảnh.</p>
            </section>

            <section id="resultSection" class="hidden space-y-6">
                
                <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-slate-800/80 border border-slate-700 p-4 rounded-xl gap-4">
                    <div class="flex items-center space-x-2 text-emerald-400 font-bold text-sm sm:text-base">
                        <i class="fa-solid fa-circle-check text-lg"></i>
                        <span>XỬ LÝ HOÀN TẤT! ĐÃ TRÍCH XUẤT ĐỦ 5 CẢNH SẠCH</span>
                    </div>
                    <a id="btnDownloadExcel" href="#" class="inline-flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-lg transition text-sm shadow-md shadow-emerald-900/20">
                        <i class="fa-solid fa-file-excel text-base"></i>
                        <span>Tải Bảng Excel Thống Kê (.CSV)</span>
                    </a>
                </div>

                <div class="bg-slate-950 border border-slate-800 rounded-xl p-5 shadow-inner">
                    <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                        <span class="text-xs font-bold tracking-widest text-slate-400 uppercase"><i class="fa-solid fa-rectangle-list mr-1"></i> Bảng Đạo Diễn Chi Tiết</span>
                        <span class="text-xs bg-slate-800 px-2 py-0.5 rounded text-indigo-400 font-medium">Bản xem trước</span>
                    </div>
                    <pre id="directorBoardText" class="text-sm text-slate-300 font-mono whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto pr-2"></pre>
                </div>
            </section>

        </main>

        <script>
            const fileInput = document.getElementById('videoFile');
            const fileStatus = document.getElementById('fileStatus');
            const uploadForm = document.getElementById('uploadForm');
            const btnSubmit = document.getElementById('btnSubmit');
            const loadingSection = document.getElementById('loadingSection');
            const loadingText = document.getElementById('loadingText');
            const resultSection = document.getElementById('resultSection');
            const directorBoardText = document.getElementById('directorBoardText');
            const btnDownloadExcel = document.getElementById('btnDownloadExcel');

            // Cập nhật tên file khi chọn xong
            fileInput.addEventListener('change', (e) => {
                if(fileInput.files.length > 0) {
                    fileStatus.innerHTML = `Đã chọn: <span class="text-indigo-400 font-bold">${fileInput.files[0].name}</span>`;
                }
            });

            // Xử lý gửi Form lên API bằng AJAX (Fetch)
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                // 1. Chuyển trạng thái giao diện sang Loading
                uploadForm.classList.add('pointer-events-none', 'opacity-50');
                loadingSection.classList.remove('hidden');
                resultSection.classList.add('hidden');
                btnSubmit.disabled = true;

                // Tạo hiệu ứng đổi chữ loading cho chuyên nghiệp
                const statusMsgs = [
                    "ĐANG TẢI VIDEO LÊN GOOGLE AI STUDIO...",
                    "GEMINI ĐANG QUAN SÁT TẠO HÌNH NHÂN VẬT GỐC...",
                    "ĐANG CỐ ĐỊNH CHÂN DUNG NHÂN VẬT QUA 5 CẢNH PROMPT...",
                    "ĐANG DỊCH THOẠI TIẾNG VIỆT VÀ CHỐNG TẠO CHỮ (NO TEXT)...",
                    "ĐANG ĐÓNG GÓI DỮ LIỆU ĐỂ XUẤT RA EXCEL..."
                ];
                let msgIdx = 0;
                const msgInterval = setInterval(() => {
                    msgIdx = (msgIdx + 1) % statusMsgs.length;
                    loadingText.innerText = statusMsgs[msgIdx];
                }, 4000);

                // 2. Chuẩn bị file để bắn lên API
                const formData = new FormData();
                formData.append("video", fileInput.files[0]);

                try {
                    const response = await fetch('/api/remake-video', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();

                    clearInterval(msgInterval);

                    if(response.ok) {
                        // 3. Hiển thị kết quả lên màn hình Web
                        directorBoardText.textContent = data.director_board;
                        btnDownloadExcel.href = `/api/download/${data.excel_file}`;
                        resultSection.classList.remove('hidden');
                    } else {
                        alert("Có lỗi xảy ra: " + (data.error || "Không rõ nguyên nhân"));
                    }
                } catch (error) {
                    clearInterval(msgInterval);
                    alert("Không thể kết nối đến Server Python backend!");
                } finally {
                    // 4. Khôi phục lại nút bấm
                    uploadForm.classList.remove('pointer-events-none', 'opacity-50');
                    loadingSection.classList.add('hidden');
                    btnSubmit.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


# =====================================================================
# 2. HỆ THỐNG XỬ LÝ BACKEND (LOGIC AI + XUẤT FILE BIỂU)
# =====================================================================
@app.post("/api/remake-video")
async def remake_video(video: UploadFile = File(...)):
    
    temp_file_path = f"temp_{video.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
        
    try:
        print("Đang tải video lên Google AI Studio...")
        uploaded_video = genai.upload_file(path=temp_file_path)
        
        while uploaded_video.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            uploaded_video = genai.get_file(uploaded_video.name)
            
        if uploaded_video.state.name == "FAILED":
            return {"error": "Lỗi xử lý video từ phía Google."}
            
        print("\nĐang phân tích, viết kịch bản và tạo dữ liệu SaaS...")
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        system_prompt = """
        Bạn là một chuyên gia kịch bản YouTube Shorts và bậc thầy tạo Prompt cho AI Google Veo 3 / Kling AI.
        Hãy xem/nghe đoạn video tôi cung cấp và thực hiện các yêu cầu NGHIÊM NGẶT sau:
        
        PHẦN 1: KỊCH BẢN MỚI (YÊU CẦU ĐÚNG 5 CẢNH)
        - Viết lại nội dung từ video gốc thành 1 kịch bản Shorts hoàn toàn mới, hấp dẫn, có Hook giật gân.
        - BẮT BUỘC chia kịch bản thành CHÍNH XÁC 5 CẢNH (Scene 1 đến Scene 5).
        - Ghi chú yêu cầu Voice: "Giọng người miền Bắc Việt Nam, trong trẻo, dễ nghe".
        
        PHẦN 2: VEO 3 PROMPTS (TIẾNG ANH + CỐ ĐỊNH NHÂN VẬT + KHÔNG TEXT)
        - CỐ ĐỊNH NHÂN VẬT: Tạo 1 cụm từ tiếng Anh mô tả ngoại hình nhân vật chi tiết và đặt ở đầu MỖI prompt của 5 cảnh.
        - KHÔNG CHỨA CHỮ VIẾT: Tuyệt đối KHÔNG yêu cầu AI tạo ra chữ, text overlay, hay tiêu đề xuất hiện trên khung hình.
        - Cấu trúc 1 câu Prompt BẮT BUỘC phải theo định dạng sau:
          [Mô tả nhân vật cố định bằng Tiếng Anh] + [Hành động/Bối cảnh Tiếng Anh] + "cinematic lighting, ultra-detailed, photorealistic, 9:16 vertical aspect ratio, shot on 35mm lens, absolutely NO TEXT, no watermark, no typography". **Lời thoại:** "[Chèn chính xác câu thoại tiếng Việt của cảnh đó vào đây]"
        
        PHẦN 3: XUẤT DỮ LIỆU BẢNG EXCEL (BẮT BUỘC ĐẶT Ở CUỐI CÙNG)
        Hãy tạo một danh sách thô gồm đúng 5 dòng tương ứng với 5 cảnh để đưa vào Excel. Phân tách Tên Cảnh, Prompt tiếng Anh, và Lời thoại bằng ký tự | (dấu gạch dọc). 
        TUYỆT ĐỐI KHÔNG dùng bảng Markdown, chỉ viết chữ thô như ví dụ dưới đây:
        Cảnh 1 | A 35-year-old Asian man... absolutely NO TEXT. | Này, bà con ơi!
        Cảnh 2 | A 35-year-old Asian man... absolutely NO TEXT. | Cứ tưởng do thiếu sắt...
        """
        
        response = model.generate_content([uploaded_video, system_prompt])
        final_result = response.text
        
        # In kết quả ra Terminal để dự phòng
        print("\n" + "="*70)
        print("DỮ LIỆU ĐÃ XỬ LÝ HOÀN TẤT:")
        print("="*70)
        print(final_result)
        print("="*70 + "\n")
        
        # Tạo file CSV/Excel Excel
        excel_filename = f"Kich_Ban_{int(time.time())}.csv"
        
        if "PHẦN 3:" in final_result:
            csv_data = final_result.split("PHẦN 3:")[1].strip()
            lines = csv_data.split('\n')
            
            with open(excel_filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Tên Cảnh', 'Prompt Video (Copy dán vào Veo/Kling)', 'Lời Thoại (Copy dán vào Capcut lồng tiếng)'])
                
                for line in lines:
                    if '|' in line:
                        row = [item.strip() for item in line.split('|')]
                        writer.writerow(row)
            
            print(f"✅ ĐÃ XUẤT THÀNH CÔNG FILE EXCEL: {excel_filename}")

        return {
            "message": "Phân tích kịch bản thành công!",
            "director_board": final_result,
            "excel_file": excel_filename
        }

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            genai.delete_file(uploaded_video.name)
        except:
            pass

# =====================================================================
# 3. ROUTE TẢI FILE EXCEL TRỰC TIẾP TỪ GIAO DIỆN WEB
# =====================================================================
@app.get("/api/download/{filename}")
async def download_file(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type='text/csv', filename=filename)
    raise HTTPException(status_code=404, detail="File không tồn tại hoặc đã bị xóa.")
sb_publishable_aP5Kx2_5ewoSaZ5dDlv5kQ_kHQV-TQe
https://xvepiudhohbqwdvpkhhx.supabase.co/rest/v1/
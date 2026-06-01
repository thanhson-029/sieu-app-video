from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import google.generativeai as genai
import time
import os
import shutil
import csv

app = FastAPI()

# 1. ANH ĐIỀN LẠI API KEY GEMINI CỦA ANH VÀO ĐÂY NHÉ
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
genai.configure(api_key=GEMINI_API_KEY)

# =====================================================================
# GIAO DIỆN WEB CHUẨN (ĐÃ KHỬ TRÙNG LẶP BIẾN SUPABASE)
# =====================================================================
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Siêu App AI Video Shorts</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
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
                
                <div id="userProfile" class="hidden flex items-center space-x-4">
                    <div class="hidden sm:flex flex-col text-right">
                        <span id="userEmail" class="text-sm font-semibold text-slate-300">Đang tải...</span>
                        <span class="text-xs text-emerald-400 font-medium"><i class="fa-solid fa-crown mr-1"></i>Gói SaaS Premium</span>
                    </div>
                    <button id="btnLogout" class="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg text-xs font-bold text-red-400 border border-slate-700 transition">
                        Đăng Xuất
                    </button>
                </div>
            </div>
        </header>

        <section id="loginSection" class="max-w-md mx-auto mt-20 bg-slate-800 p-8 rounded-2xl shadow-xl border border-slate-700">
            <h2 class="text-2xl font-bold text-center mb-2 text-white">Đăng Nhập Hệ Thống</h2>
            <p class="text-sm text-center text-slate-400 mb-6">Chỉ dành cho thành viên được cấp quyền</p>
            <form id="loginForm" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-400 mb-1">Email Tài Khoản</label>
                    <input type="email" id="emailInput" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-400 mb-1">Mật Khẩu</label>
                    <input type="password" id="passwordInput" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500" required>
                </div>
                <button type="submit" id="btnLogin" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-4 rounded-lg transition mt-4">
                    Đăng Nhập
                </button>
                <p id="loginError" class="text-red-400 text-sm text-center hidden mt-2"></p>
            </form>
        </section>

        <main id="appSection" class="hidden max-w-4xl mx-auto px-4 py-10">
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
                        </div>
                    </div>
                    <button type="submit" id="btnSubmit" class="w-full bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold py-3.5 px-4 rounded-xl transition shadow-lg flex items-center justify-center space-x-2">
                        <i class="fa-solid fa-bolt"></i>
                        <span>Bắt Đầu Phân Tích & Remake Video</span>
                    </button>
                </form>
            </section>

            <section id="loadingSection" class="hidden text-center py-12 bg-slate-800/20 rounded-2xl border border-slate-800/50 space-y-4">
                <div class="inline-block animate-spin text-indigo-500 text-4xl"><i class="fa-solid fa-circle-notch"></i></div>
                <div class="text-indigo-400 font-bold tracking-wider text-sm animate-pulse">ĐANG TẢI VIDEO LÊN GOOGLE AI STUDIO...</div>
            </section>

            <section id="resultSection" class="hidden space-y-6">
                <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-slate-800/80 border border-slate-700 p-4 rounded-xl gap-4">
                    <div class="flex items-center space-x-2 text-emerald-400 font-bold text-sm sm:text-base">
                        <i class="fa-solid fa-circle-check text-lg"></i>
                        <span>XỬ LÝ HOÀN TẤT! ĐÃ TRÍCH XUẤT ĐỦ 5 CẢNH SẠCH</span>
                    </div>
                    <a id="btnDownloadExcel" href="#" class="inline-flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-lg transition text-sm">
                        <i class="fa-solid fa-file-excel text-base"></i>
                        <span>Tải Bảng Excel Thống Kê (.CSV)</span>
                    </a>
                </div>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-5 shadow-inner">
                    <pre id="directorBoardText" class="text-sm text-slate-300 font-mono whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto pr-2"></pre>
                </div>
            </section>
        </main>

        <script>
            // ĐỊA CHỈ KÉT SẮT (EM ĐÃ ĐIỀN SẴN LINK CHO ANH)
            const S_URL = "https://xvepiudhohbqwdvpkhhx.supabase.co";
            
            // 2. ANH CHỈ CẦN DÁN CÁI MÃ KHÓA PUBLISHABLE KEY VÀO ĐÂY NHÉ:
            const S_KEY = "sb_publishable_aP5Kx2_5ewoSaZ5dDlv5kQ_kHQV-TQe";
            
            // Khởi tạo hệ thống với tên biến độc nhất, không lo bị trùng lặp
            const mienNamDocNhatSupabase = window.supabase.createClient(S_URL, S_KEY);

            const loginSection = document.getElementById('loginSection');
            const appSection = document.getElementById('appSection');
            const userProfile = document.getElementById('userProfile');
            const userEmail = document.getElementById('userEmail');
            const loginError = document.getElementById('loginError');

            mienNamDocNhatSupabase.auth.onAuthStateChange((event, session) => {
                if (session) {
                    loginSection.classList.add('hidden');
                    appSection.classList.remove('hidden');
                    userProfile.classList.remove('hidden');
                    userEmail.innerText = session.user.email;
                } else {
                    loginSection.classList.remove('hidden');
                    appSection.classList.add('hidden');
                    userProfile.classList.add('hidden');
                }
            });

            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = document.getElementById('emailInput').value;
                const password = document.getElementById('passwordInput').value;
                document.getElementById('btnLogin').innerText = "Đang kiểm tra...";

                const { data, error } = await mienNamDocNhatSupabase.auth.signInWithPassword({ email, password });

                if (error) {
                    loginError.innerText = "Sai email hoặc mật khẩu! Vui lòng liên hệ Admin.";
                    loginError.classList.remove('hidden');
                    document.getElementById('btnLogin').innerText = "Đăng Nhập";
                }
            });

            document.getElementById('btnLogout').addEventListener('click', async () => {
                await mienNamDocNhatSupabase.auth.signOut();
            });

            const fileInput = document.getElementById('videoFile');
            const fileStatus = document.getElementById('fileStatus');
            const uploadForm = document.getElementById('uploadForm');
            const btnSubmit = document.getElementById('btnSubmit');
            const loadingSection = document.getElementById('loadingSection');
            
            fileInput.addEventListener('change', () => {
                if(fileInput.files.length > 0) fileStatus.innerHTML = `Đã chọn: <span class="text-indigo-400 font-bold">${fileInput.files[0].name}</span>`;
            });

            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                uploadForm.classList.add('pointer-events-none', 'opacity-50');
                loadingSection.classList.remove('hidden');
                btnSubmit.disabled = true;

                const formData = new FormData();
                formData.append("video", fileInput.files[0]);

                try {
                    const response = await fetch('/api/remake-video', { method: 'POST', body: formData });
                    const data = await response.json();
                    if(response.ok) {
                        document.getElementById('directorBoardText').textContent = data.director_board;
                        document.getElementById('btnDownloadExcel').href = `/api/download/${data.excel_file}`;
                        document.getElementById('resultSection').classList.remove('hidden');
                    } else {
                        alert("Lỗi: " + data.error);
                    }
                } catch (error) {
                    alert("Mất kết nối máy chủ!");
                } finally {
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

@app.post("/api/remake-video")
async def remake_video(video: UploadFile = File(...)):
    temp_file_path = f"temp_{video.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    try:
        uploaded_video = genai.upload_file(path=temp_file_path)
        while uploaded_video.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_video = genai.get_file(uploaded_video.name)
            
        if uploaded_video.state.name == "FAILED":
            return {"error": "Lỗi xử lý video từ phía Google."}
            
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        system_prompt = """
        Bạn là chuyên gia kịch bản YouTube Shorts.
        PHẦN 1: KỊCH BẢN MỚI (5 CẢNH)
        PHẦN 2: VEO 3 PROMPTS (CỐ ĐỊNH NHÂN VẬT + KHÔNG TEXT)
        [Mô tả nhân vật cố định] + [Hành động] + "cinematic lighting, ultra-detailed, 9:16 vertical, NO TEXT". **Lời thoại:** "[Chèn thoại Tiếng Việt]"
        PHẦN 3: XUẤT DỮ LIỆU BẢNG EXCEL
        Cảnh 1 | A 35-year-old Asian man... NO TEXT. | Này, bà con ơi!
        """
        response = model.generate_content([uploaded_video, system_prompt])
        final_result = response.text
        
        excel_filename = f"Kich_Ban_{int(time.time())}.csv"
        if "PHẦN 3:" in final_result:
            csv_data = final_result.split("PHẦN 3:")[1].strip()
            lines = csv_data.split('\n')
            with open(excel_filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Tên Cảnh', 'Prompt Video', 'Lời Thoại'])
                for line in lines:
                    if '|' in line:
                        writer.writerow([item.strip() for item in line.split('|')])
        return {"message": "Thành công!", "director_board": final_result, "excel_file": excel_filename}
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        try: genai.delete_file(uploaded_video.name)
        except: pass

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type='text/csv', filename=filename)
    raise HTTPException(status_code=404, detail="File không tồn tại.")
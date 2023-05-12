@echo off
echo ===Setting up virtual environment...===
python -m venv .venv
call .\.venv\Scripts\activate

echo ===Installing dependencies...===
echo Select pytoch for your CUDA version
echo 1. NONE (CPU only)
echo 2. 11.7
echo 3. 11.8
echo 4. Don't install pytorch

:select_cuda

set /p cuda=Enter your choice: 

goto cuda_%cuda%

echo "Invalid choice"
goto select_cuda

:cuda_1
pip3 install torch torchvision torchaudio
pip3 install -r requirements.txt
goto end

:cuda_2
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
pip3 install -r requirements.txt
goto end

:cuda_3
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install -r requirements.txt
goto end

:cuda_4
echo ===Skipping pytorch installation===
FOR /F %%k IN ('findstr /V /B "#" .\requirements.txt') DO ( IF NOT torch==%%k IF NOT torchvision==%%k IF NOT torchaudio==%%k ( pip install %%k ) ELSE ( echo Skipping %%k ) )
goto end

:end
echo ===Setup complete!===
# Windows 설치·사용 가이드

이 문서 하나만 그대로 따라 하면 **Windows에서** 설치부터 첫 결과 영상을
만드는 것까지 끝낼 수 있습니다. macOS 관련 내용은 이 문서에 없습니다
(macOS는 `docs/SETUP_MAC.md` 참고).

> 프로그래밍을 몰라도 됩니다. 아래 명령어를 복사해서 PowerShell에
> 붙여넣고 Enter를 누르는 것이 전부입니다.

| 단계 | 내용 | 스크립트 |
|---|---|---|
| 1 | 첫 프레임에서 사람 위치를 클릭으로 지정해 마스크 생성 | `hugging_face/app.py` (Gradio 데모) |
| 2 | 영상 전체에서 알파 매트(투명도) + 전경 영상 추출 | `inference_matanyone2.py` |
| 3 | 알파 매트를 AI 배경 플레이트와 합성 | `composite.py` |

**전체 흐름**: 원본 영상 → ①Gradio 데모에서 클릭으로 첫 프레임 마스크 생성 →
②`inference_matanyone2.py`로 알파 매트/전경 영상 추출 → ③`composite.py`로
알파 매트 + 새 배경 → 합성된 결과 영상.

---

## 0. 미리 알아둘 것 (Windows)

- 아래 명령어는 **PowerShell** 기준입니다. 시작 메뉴에서 "PowerShell"을
  검색해서 실행하세요 (관리자 권한은 필요 없습니다).
- **NVIDIA GPU(그래픽카드)가 있는 컴퓨터**를 권장합니다. GPU가 없어도 설치와
  마스크 생성까지는 가능하지만, 실제 매팅 연산(②, ③번)은 매우 느리거나
  사실상 어렵습니다.
- ⚠️ **현재 코드의 알려진 제약사항**: `inference_matanyone2.py`가 내부적으로
  쓰는 자동 장치 선택 함수(`matanyone2/utils/device.py`의
  `get_default_device()`)는 지금 **mps(Apple Silicon 전용) → cpu 순서로만
  시도하고, cuda(NVIDIA GPU)는 검사하지 않습니다.** 실제로 확인한 내용입니다:
  이 컴퓨터에 NVIDIA GPU가 있고 `torch.cuda.is_available()`이 `True`를
  반환하더라도, `inference_matanyone2.py`는 **항상 CPU로 실행**됩니다. Windows
  환경에는 mps 자체가 존재하지 않으므로 이 함수는 cuda 유무와 상관없이
  cpu로 떨어집니다. 이 문서는 코드를 수정하지 않고 **현재 동작을 있는
  그대로** 안내합니다 — 영상 처리가 예상보다 느리다면 이 제약 때문일 가능성이
  높습니다.
- 인터넷에서 파일을 여러 개 받습니다(모델 가중치 파일들, 합쳐서 약 1GB
  안팎). 회사 네트워크가 외부 접속을 막고 있다면 아래 "문제 해결" 항목을
  참고하세요.

---

## 1. Python 설치

1. https://www.python.org/downloads/windows/ 접속
2. "Windows installer (64-bit)" 링크로 설치 파일 받기 (3.10 이상 필요)
3. 설치 파일 실행 시, **첫 화면 아래쪽의 "Add python.exe to PATH" 체크박스를
   반드시 체크**한 뒤 "Install Now" 클릭
4. 설치가 끝나면 PowerShell에서 확인:
   ```powershell
   python --version
   ```
   `Python 3.10.x` 이상이 출력되면 성공입니다.

## 2. Git 설치

1. https://git-scm.com/downloads/win 에서 설치 파일 다운로드 후 실행
   (설치 중 옵션은 전부 기본값으로 "Next"만 눌러도 됩니다)
2. 설치 확인:
   ```powershell
   git --version
   ```
   버전이 출력되면 성공입니다.

## 3. Miniforge 설치 (가상환경용 conda)

이 프로젝트는 파이썬 패키지들을 컴퓨터의 다른 프로그램과 섞이지 않게
가상환경(격리된 폴더)에 설치합니다. 이를 위해 [Miniforge](https://github.com/conda-forge/miniforge)(가벼운
conda 배포판)를 설치합니다.

1. https://github.com/conda-forge/miniforge/releases/latest 접속
2. 자산(Assets) 목록에서 **`Miniforge3-Windows-x86_64.exe`** 다운로드
3. 설치 파일 실행 → 기본 옵션대로 "Next" 진행 (계정용 설치 권장, "Just Me")
   - 설치 마지막 화면에서 "Add Miniforge3 to my PATH environment variable"
     체크박스는 **선택 사항**입니다. 체크 안 해도 상관없습니다 — 대신 앞으로는
     시작 메뉴의 **"Miniforge Prompt"**를 사용해서 명령어를 입력합니다.
4. 설치가 끝나면 시작 메뉴에서 **"Miniforge Prompt"**를 실행하고 확인:
   ```powershell
   conda --version
   ```
   버전이 출력되면 성공입니다. **이후 이 문서의 모든 명령어는 이
   "Miniforge Prompt" 창에서 실행**합니다.

## 4. 이 저장소 받기 (Clone)

Miniforge Prompt에서, 코드를 저장하고 싶은 폴더로 이동한 뒤 실행합니다.
예를 들어 바탕화면에 받고 싶다면:

```powershell
cd Desktop
git clone https://github.com/workseok/matanyone2.git
cd matanyone2
```

## 5. 가상환경 생성

```powershell
conda create -n matanyone2 python=3.10 -y
conda activate matanyone2
```

프롬프트 맨 앞이 `(matanyone2)`로 바뀌면 가상환경이 활성화된 것입니다.
앞으로 Miniforge Prompt 창을 새로 열 때마다 `conda activate matanyone2`를
다시 실행해야 합니다.

## 6. 의존성 설치

```powershell
pip install -e .
pip install -r hugging_face/requirements.txt
```

- 첫 번째 줄: 핵심 매팅 패키지 설치 (torch 포함, Windows용 wheel이 자동으로
  선택되어 받아집니다)
- 두 번째 줄: Gradio 데모(클릭 마스크) 실행용 패키지

설치가 끝나면 확인:
```powershell
python -c "import torch, matanyone2, gradio; print('설치 확인 완료')"
```
`설치 확인 완료`가 출력되면 성공입니다.

> **참고**: 이 저장소를 준비한 환경(리눅스, uv 사용)에서는 위 두 `pip
> install` 명령이 정상적으로 끝나는 것을 확인했지만, Windows +
> Miniforge 조합으로 직접 실행해 검증하지는 못했습니다. `pycocotools`,
> `cchardet`처럼 C로 빌드되는 일부 패키지는 Windows에서 컴파일러가 없으면
> 설치가 실패할 수 있습니다 — 에러가 나면 아래 "문제 해결"의 "Microsoft
> C++ Build Tools" 항목을 참고하세요.

---

## 7. Gradio 데모로 첫 프레임 마스크 만들기

```powershell
cd hugging_face
python app.py
```

처음 실행하면 SAM 체크포인트(약 2.4GB)와 MatAnyone2 체크포인트를 인터넷에서
받느라 몇 분 걸릴 수 있습니다. 아래처럼 출력되면 정상입니다.

```
Running on local URL:  http://127.0.0.1:7860
Running on public URL: https://xxxxxxxxxxxxxxxx.gradio.live
```

같은 컴퓨터에서만 쓸 거라면 `Running on local URL`에 나온 주소를 브라우저에
입력해서 열면 됩니다 (다른 프로그램이 이미 7860 포트를 쓰고 있으면 gradio가
자동으로 7861, 7862 등 다음 번호를 씁니다). 코드의 `--port` 옵션은 도움말에는
있지만 실제 실행에는 연결되어 있지 않아 현재는 효과가 없습니다.

### 7-1. 화면 구성 (스크린샷 대신 화면 설명)

> ⚠️ 이 문서를 준비한 환경은 GPU가 없고 모델 체크포인트 다운로드도 막혀
> 있어서, 실제로 데모를 띄워 화면을 캡처해볼 수는 없었습니다. 대신 코드에
> 실제로 들어있는 화면 요소 이름을 그대로 옮겨 적었으니, 실행했을 때 보이는
> 화면과 아래 설명의 버튼/라벨 이름이 정확히 일치할 것입니다.

화면 위쪽에 **"Video"** 탭과 **"Image"** 탭이 있습니다. 영상을 다룰 것이므로
**"Video"** 탭을 선택한 상태로 아래를 따라 합니다.

1. **Model Selection**: `MatAnyone2`가 기본 선택되어 있습니다 (그대로 두면 됨).
2. **Step1: Upload video** — 왼쪽의 **"Input Video"** 칸에 영상 파일을
   끌어다 놓거나 클릭해서 선택한 뒤, 그 아래 **"Load Video"** 버튼을 누릅니다.
   - 누르면 영상 정보(길이, 프레임 수 등)와 함께, 화면에 **"Start Frame"**이라는
     이름의 정지 이미지(영상의 첫 프레임)가 나타납니다.
3. **Step2: Add masks** — 라벨에 "여러 번 클릭한 뒤 **Add Mask**를 한 번
   누르세요"라고 안내가 붙어 있습니다.
   - **Start Frame** 이미지 위에서, 합성하고 싶은 사람(피사체)을 마우스로
     클릭합니다. 클릭할 때마다 그 지점에 점이 찍히고, 모델이 실시간으로 추정한
     마스크가 반투명하게 덧씌워져 보입니다.
   - 화면 중간의 **"Point Prompt"** 라디오 버튼이 `Positive`(기본값)로 되어
     있으면 클릭한 지점이 "이 부분은 피사체다"라는 뜻이고, `Negative`로
     바꾼 뒤 클릭하면 "이 부분은 피사체가 아니다"라는 뜻입니다. 마스크가
     원하는 영역을 벗어나면 `Negative`로 바꿔서 그 부분을 클릭해 제외시킬 수
     있습니다.
   - 클릭을 잘못했다면 **"Clear Clicks"** 버튼으로 지금까지의 클릭을 모두
     지우고 다시 시작할 수 있습니다.
   - 마스크 모양이 마음에 들면 **"Add Mask"** 버튼을 눌러 확정합니다 (사람이
     여러 명이면 이 과정을 반복해서 여러 개의 마스크를 추가할 수 있습니다).
   - **"Model Settings (click to expand)"**를 펼치면 `Erode Kernel Size` /
     `Dilate Kernel Size`(마스크 경계를 얼마나 깎거나 넓힐지, 기본값 10)를
     조절할 수 있습니다. 잘 모르겠으면 기본값 그대로 두면 됩니다.
4. **Video Matting** 버튼을 누르면 전체 영상에 대해 매팅이 실행됩니다
   (위 "0. 미리 알아둘 것"의 제약 때문에 이 컴퓨터에 NVIDIA GPU가 있어도
   현재는 CPU로 돌아갑니다 — 영상 길이에 따라 수 분~수십 분 걸릴 수
   있습니다).
5. 완료되면 **"Foreground Output"**(전경만 남긴 영상)과 **"Alpha Output"**(흑백
   알파 매트 영상)이 화면에 나타나고, 그 아래 각각 **"Foreground Output"** /
   **"Alpha Mask Output"** 버튼으로 파일을 내려받을 수 있습니다.

> **이 데모만으로 충분한 경우**: 위 5단계까지만 해도 알파/전경 영상이 이미
> 다 나옵니다. 아래 8번(`inference_matanyone2.py`)은 **데모 화면 없이,
> 명령어만으로** 같은 작업을 자동화/반복 처리하고 싶을 때 씁니다 — 이미
> 갖고 있는 마스크 이미지 파일(`.png`)이 있다면 데모를 켜지 않고 바로 8번으로
> 넘어가도 됩니다. 이 저장소의 `inputs\mask\` 폴더에는 테스트용 마스크가 이미
> 들어있어서, 데모 없이도 바로 시험해볼 수 있습니다.

---

## 8. `inference_matanyone2.py`로 알파 매트/전경 영상 뽑기

이미 첫 프레임 마스크(`.png` 파일)가 있다면, 명령어 한 줄로 영상 전체의
알파 매트와 전경 영상을 뽑을 수 있습니다. 이 저장소에는 바로 시험해볼 수 있는
예시 영상/마스크가 `inputs\` 폴더에 이미 들어있습니다. `matanyone2` 저장소
폴더로 돌아온 뒤(`cd ..`) 실행하세요.

```powershell
python inference_matanyone2.py -i inputs/video/test-sample2.mp4 -m inputs/mask/test-sample2.png
```

- 입력이 개별 프레임 이미지들이 든 폴더(`inputs/video/test-sample1`처럼)여도
  똑같이 동작합니다:
  ```powershell
  python inference_matanyone2.py -i inputs/video/test-sample1 -m inputs/mask/test-sample1.png
  ```
- 처음 실행할 때 모델 체크포인트(`matanyone2.pth`, 약 140MB)를
  `pretrained_models\` 폴더로 자동 다운로드합니다. 이후 실행부터는 다시
  받지 않습니다.
- 결과는 기본적으로 `results\` 폴더에 아래 두 파일로 저장됩니다:
  - `results\test-sample2_fgr.mp4` — 전경(사람)을 초록 배경 위에 얹은 미리보기 영상
  - `results\test-sample2_pha.mp4` — 알파 매트(흑백, 사람=흰색/배경=검은색) 영상
  - 이 중 **`*_pha.mp4`가 다음 단계(`composite.py`)에서 쓰는 파일**입니다.

### 자주 쓰는 옵션

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `-i`, `--input_path` | 입력 영상(.mp4/.mov/.avi) 또는 프레임 폴더 경로 | `inputs/video/test-sample1` |
| `-m`, `--mask_path` | 첫 프레임 마스크(.png) 경로 | `inputs/mask/test-sample1.png` |
| `-o`, `--output_path` | 결과를 저장할 폴더 | `results/` |
| `-c`, `--ckpt_path` | 모델 체크포인트 경로 | `pretrained_models/matanyone2.pth` |
| `-w`, `--warmup` | 첫 프레임 알파를 안정화시키기 위한 워밍업 반복 횟수 | `10` |
| `-e`, `--erode_kernel` | 입력 마스크 경계를 깎는 정도 | `10` |
| `-d`, `--dilate_kernel` | 입력 마스크 경계를 넓히는 정도 | `10` |
| `--suffix` | 결과 파일 이름에 붙일 구분자 (예: 사람이 여러 명일 때 `target1`) | (없음) |
| `--save_image` | mp4 대신(과 함께) 프레임별 PNG로도 저장 | 꺼짐 |
| `--max_size` | 지정하면 짧은 변 기준 이 크기를 넘을 때 다운샘플링 | `-1` (제한 없음) |

프레임별 이미지도 함께 받고 싶다면:
```powershell
python inference_matanyone2.py -i inputs/video/test-sample2.mp4 -m inputs/mask/test-sample2.png --save_image
```
이 경우 `results\test-sample2\pha\0000.png`, `results\test-sample2\fgr\0000.png`
형태로 프레임마다 개별 파일이 추가로 저장됩니다.

---

## 9. `composite.py`로 AI 배경과 합성하기

7번(Gradio 데모) 또는 8번(`inference_matanyone2.py`)에서 나온 **알파 매트**와,
원본 영상, 그리고 새로 넣고 싶은 **배경 이미지(또는 배경 영상)**를 합쳐서
최종 결과 영상을 만듭니다. 공식은 다음과 같습니다 (알파값 1=사람, 0=배경):

```
결과 = 원본영상 × 알파 + 새배경 × (1 − 알파)
```

### 기본 사용법

```powershell
python composite.py -f inputs/video/test-sample2.mp4 -a results/test-sample2_pha.mp4 -b path/to/ai_background.jpg -o results/test-sample2_composite.mp4
```

### 옵션

| 옵션 | 필수 | 설명 |
|---|---|---|
| `-f`, `--fg` | ✅ | 원본 전경 영상. `inference_matanyone2.py`에 넣었던 **바로 그 입력**(영상 파일 또는 프레임 폴더)을 그대로 지정합니다. |
| `-a`, `--alpha` | ✅ | 알파 매트. `inference_matanyone2.py`가 만든 `*_pha.mp4`를 지정하거나, `--save_image`로 저장했다면 `pha\` 프레임 폴더를 지정해도 됩니다. |
| `-b`, `--bg` | ✅ | 새로 넣을 배경. **정지 이미지**를 주면 영상 길이 내내 그 이미지 한 장이 유지되고, **영상**을 주면 길이가 맞지 않을 때 자동으로 반복하거나(짧으면) 잘라서(길면) 맞춥니다. |
| `-o`, `--output` | ✅ | 결과 영상을 저장할 경로 (mp4). |
| `--fps` | ❌ | 결과 영상의 프레임 속도를 강제로 지정. 생략하면 `-f`로 넣은 원본 영상의 fps를 그대로 씁니다. |

### 예시

**정지 이미지 배경으로 합성**:
```powershell
python composite.py -f inputs/video/test-sample2.mp4 -a results/test-sample2_pha.mp4 -b assets/ai_backgrounds/beach.jpg -o results/test-sample2_beach.mp4
```

**영상 배경으로 합성**:
```powershell
python composite.py -f inputs/video/test-sample2.mp4 -a results/test-sample2_pha.mp4 -b assets/ai_backgrounds/aurora_loop.mp4 -o results/test-sample2_aurora.mp4
```

**`--save_image`로 저장한 프레임 폴더를 입력으로 쓸 때**:
```powershell
python composite.py -f inputs/video/test-sample1 -a results/test-sample1/pha -b assets/ai_backgrounds/studio.jpg -o results/test-sample1_studio.mp4
```

> `-f`(원본 영상)와 `-a`(알파 매트)의 **프레임 개수가 서로 다르면 오류가
> 납니다** — 반드시 같은 실행에서 나온 원본/알파 조합을 짝지어 주세요.

---

## 10. 전체 파이프라인 한 번에 따라 해보기 (테스트 영상 기준)

이 저장소에 포함된 예시 영상(`test-sample2.mp4`)으로 처음부터 끝까지 한 번
따라 해볼 수 있는 명령어 모음입니다 (Miniforge Prompt에서, `conda activate
matanyone2` 상태로).

```powershell
# 1) 알파 매트 + 전경 영상 추출 (이미 있는 예시 마스크 사용)
python inference_matanyone2.py -i inputs/video/test-sample2.mp4 -m inputs/mask/test-sample2.png

# 2) 새 배경과 합성 (배경 이미지는 직접 준비해서 경로를 바꿔주세요)
python composite.py -f inputs/video/test-sample2.mp4 -a results/test-sample2_pha.mp4 -b my_background.jpg -o results/test-sample2_final.mp4
```

`results\test-sample2_final.mp4`를 재생해서 결과를 확인하면 됩니다. 직접
찍은 영상을 쓰고 싶다면, 1)번 명령의 `-i` 값을 그 영상 경로로 바꾸고, `-m`
값은 7번(Gradio 데모)에서 클릭으로 만든 마스크(또는 직접 그린 흑백 마스크
이미지, 흰색=사람/검은색=배경)로 바꿔서 실행하면 됩니다.

---

## 11. 문제 해결 (Troubleshooting) — Windows

**`python` 또는 `conda` 명령을 찾을 수 없다는 오류가 날 때**
→ Python 설치 시 "Add python.exe to PATH" 체크를 빠뜨렸거나, Miniforge Prompt가
아닌 일반 PowerShell/명령 프롬프트를 쓰고 있을 가능성이 있습니다. `conda`
명령은 반드시 시작 메뉴의 **"Miniforge Prompt"**에서 실행하세요.

**`pip install -e .` 또는 `pip install -r hugging_face/requirements.txt` 도중
`error: Microsoft Visual C++ 14.0 or greater is required` 같은 오류가 날 때**
→ `pycocotools`, `cchardet` 등 일부 패키지는 Windows에서 C/C++ 컴파일러가
필요합니다. [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)를
받아 설치할 때 "C++를 사용한 데스크톱 개발" 워크로드를 체크하고 설치한 뒤,
Miniforge Prompt를 새로 열어 `pip install` 명령을 다시 실행하세요.

**모델 체크포인트 다운로드가 멈추거나 `403`/연결 오류가 날 때**
→ 회사 네트워크가 아래 주소로 나가는 접속을 막고 있을 수 있습니다.
- `download.pytorch.org` (ResNet 백본 가중치)
- `dl.fbaipublicfiles.com` (Gradio 데모의 SAM 체크포인트)
- `github.com`의 릴리스 파일 (`matanyone2.pth`)

IT 담당자에게 위 주소들에 대한 접속을 허용해달라고 요청하거나, 막혀 있지
않은 개인 네트워크(핫스팟 등)에서 처음 한 번만 실행해서 체크포인트를 받아
두면, 그다음부터는 로컬에 저장된 파일을 그대로 쓰므로 다시 받지 않습니다.

**NVIDIA GPU가 있는데도 실행이 너무 느릴 때**
→ 위 "0. 미리 알아둘 것"에서 설명한 대로, 현재 이 저장소의 자동 장치 선택
로직은 Windows에서 CUDA를 확인하지 않고 항상 CPU를 사용합니다 (확인된
동작이며, 이 문서에서는 코드를 고치지 않습니다). GPU를 실제로 쓰려면 코드
수정이 필요한 별도 작업이니, 필요하면 개발자에게 이 문서의 "0. 미리 알아둘
것" 항목을 전달해 주세요. 우선은 `-i`로 더 짧은 테스트 영상을 시도해 보세요.

**`composite.py` 실행 시 "Foreground frame count (...) does not match alpha
frame count (...)" 오류가 날 때**
→ `-f`(원본 영상)와 `-a`(알파 매트)가 서로 다른 실행에서 나온 조합입니다.
같은 `inference_matanyone2.py` 실행 한 번에서 나온 원본 입력과 `*_pha.mp4`를
짝지어서 다시 지정하세요.

**Gradio 데모(`app.py`)를 실행했는데 브라우저 창이 자동으로 안 뜰 때**
→ 터미널에 출력된 `Running on local URL: http://127.0.0.1:7860` 주소를
직접 복사해서 브라우저 주소창에 붙여넣으면 됩니다.

**PowerShell에서 `.venv\Scripts\Activate.ps1`을 실행할 때 "이 시스템에서
스크립트를 실행할 수 없으므로..." 라는 오류가 날 때** (이 문서의 기본
경로인 conda 대신 `uv`로 가상환경을 만든 경우에만 해당)
→ PowerShell의 스크립트 실행 정책 때문입니다. PowerShell을 관리자 권한으로
열고 아래 명령을 한 번 실행하면 해결됩니다:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 참고: 이 저장소에 포함된 예시 데이터

| 경로 | 내용 |
|---|---|
| `inputs\video\test-sample1\` | 30장의 프레임 이미지로 구성된 짧은 테스트 영상 |
| `inputs\video\test-sample2.mp4` | mp4 형식의 테스트 영상 |
| `inputs\mask\test-sample1.png`, `test-sample2.png` | 각 테스트 영상의 첫 프레임 마스크 (미리 준비되어 있어 데모 없이 바로 시험 가능) |

`pretrained_models\`, `results\`는 용량이 크고 사람이 나온 영상/이미지를
포함할 수 있어 `.gitignore`에 등록되어 있습니다 (실수로 공개 저장소에
올라가지 않도록 하는 안전장치입니다).

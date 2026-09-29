# MatAnyone2 배경 합성 파이프라인

영상에서 사람(피사체)만 정확하게 뽑아내고(**비디오 매팅**, video matting), 그
결과를 AI가 만든 새 배경과 합성하는 저장소입니다. [pq-yang/MatAnyone2](https://github.com/pq-yang/MatAnyone2)
원본 코드를 그대로 가져와 쓰고, 배경 합성 스크립트(`composite.py`)만 이
저장소에서 새로 추가했습니다.

| 단계 | 내용 | 스크립트 |
|---|---|---|
| 1 | 첫 프레임에서 사람 위치를 클릭으로 지정해 마스크 생성 | `hugging_face/app.py` (Gradio 데모) |
| 2 | 영상 전체에서 알파 매트(투명도) + 전경 영상 추출 | `inference_matanyone2.py` |
| 3 | 알파 매트를 AI 배경 플레이트와 합성 | `composite.py` |

**전체 흐름**: 원본 영상 → ①Gradio 데모에서 클릭으로 첫 프레임 마스크 생성 →
②`inference_matanyone2.py`로 알파 매트/전경 영상 추출 → ③`composite.py`로
알파 매트 + 새 배경 → 합성된 결과 영상.

## 설치·사용 가이드

설치부터 실행까지 전체 순서는 운영체제별 문서를 참고하세요. 각 문서
하나만 처음부터 끝까지 따라 하면 됩니다 (Git/Python/Miniforge 설치 →
저장소 clone → 가상환경 생성 → 의존성 설치 → 실행).

- 🪟 **Windows 사용자**: [docs/SETUP_WINDOWS.md](docs/SETUP_WINDOWS.md)
- 🍎 **macOS 사용자**: [docs/SETUP_MAC.md](docs/SETUP_MAC.md)

저장소와 코드는 운영체제와 무관하게 하나로 유지됩니다 — 위 두 문서는
설치 절차와 GPU(CUDA/MPS) 관련 안내만 운영체제별로 나눠서 설명합니다.

## 저장소 구성

| 경로 | 내용 |
|---|---|
| `hugging_face/app.py` | 클릭 기반 첫 프레임 마스크 생성 + 매팅 Gradio 데모 |
| `inference_matanyone2.py` | 커맨드라인으로 알파 매트/전경 영상 추출 |
| `composite.py` | 알파 매트 + AI 배경 플레이트 합성 (이 저장소에서 새로 추가) |
| `inputs/` | 바로 시험해볼 수 있는 예시 영상/마스크 |
| `docs/SETUP_WINDOWS.md` | Windows 설치·사용 가이드 |
| `docs/SETUP_MAC.md` | macOS 설치·사용 가이드 |
| `docs/EVAL.md` | 평가(evaluation) 코드 문서 |

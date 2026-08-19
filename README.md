# Loop Engineering 포메라니안 스케치 데모

Codex가 Generator, Evaluator, Prompt Refiner 역할을 반복하며 실제 포메라니안 사진과 구조적으로 닮은 간단한 손그림 스케치를 만들어 가는 Loop Engineering 데모입니다.

목표는 사실적인 그림을 만드는 것이 아니라, 원·선·삼각형 같은 단순한 형태와 느슨한 외곽선을 유지하면서 얼굴 비율, 귀의 크기와 위치, 눈과 코의 위치, 머리와 몸의 비율, 자세, 실루엣, 구도를 점진적으로 개선하는 것입니다.

## 핵심 실행 흐름

각 iteration은 다음 순서로 진행됩니다.

```text
원본 포메라니안 사진 + 현재 Best-so-far + 현재 프롬프트
-> Generator가 후보 3개 생성
-> Evaluator가 후보를 각각 독립 평가
-> 해당 iteration의 최고 점수 후보 선택
-> 기존 Best-so-far와 비교
-> Best-so-far 갱신 또는 유지
-> Prompt Refiner가 다음 프롬프트 작성
-> 다음 iteration
```

역할 실행 순서는 항상 다음과 같습니다.

```text
Generator -> Evaluator -> Prompt Refiner
```

## Best-of-N 후보 생성

현재 프로젝트는 iteration마다 정확히 3개의 실제 후보를 생성합니다.

```text
candidate_01.png
candidate_02.png
candidate_03.png
```

Evaluator는 각 후보를 원본 사진과 독립적으로 비교하여 점수를 계산합니다. 가장 높은 `overall_score`를 받은 후보가 그 iteration의 `selected.png`가 됩니다.

평가 항목은 얼굴 비율, 귀, 눈과 코의 위치, 머리와 몸의 비율, 자세, 실루엣, 구도, 스케치 스타일 및 전체 형태 유사도입니다. 실제 결과에 따라 iteration 점수는 오르거나 내려갈 수 있으며, 점수 상승 추세를 만들기 위해 값을 인위적으로 조정하지 않습니다.

## Best-so-far 유지 방식

각 iteration에서 선택된 후보는 이전까지의 Best-so-far와 다시 비교됩니다.

- 새 후보의 점수가 더 높으면 Best-so-far를 새 후보로 갱신합니다.
- 새 후보의 점수가 같거나 낮으면 이전 Best-so-far를 그대로 유지합니다.
- 현재 iteration의 점수는 감소할 수 있지만 Best-so-far 점수는 감소하지 않습니다.
- 다음 프롬프트의 개선 기준은 단순히 가장 최근 후보가 아니라 현재 Best-so-far 결과입니다.

예시는 다음과 같습니다.

```text
Iteration 점수: 57 -> 64 -> 61 -> 70 -> 68 -> 75
Best-so-far:    57 -> 64 -> 64 -> 70 -> 70 -> 75
```

## `루프 N번해` 실행 규칙

Codex에게 `루프 5번해`, `루프 3번 실행해`, `5 iteration 돌려`처럼 요청하면 숫자 N은 **추가로 실행할 iteration 수**를 의미합니다.

기본 동작은 다음과 같습니다.

1. 최신의 성공적으로 완료된 Best-of-N run이 있으면 그 run을 이어갑니다.
2. 마지막 iteration 다음 번호부터 N개 iteration을 추가합니다.
3. 마지막 `next_prompt.txt`를 다음 iteration의 시작 프롬프트로 사용합니다.
4. 기존 iteration 결과를 삭제하거나 덮어쓰거나 번호를 다시 매기지 않습니다.
5. 실제 누적 iteration 번호에 맞는 refinement 강도를 적용합니다.

다음 경우에는 새 run을 시작합니다.

- 성공적으로 완료된 Best-of-N run이 없는 경우
- 최신 결과가 과거의 legacy 단일 이미지 형식인 경우
- 사용자가 `새 run으로 시작해`라고 명시한 경우

요청한 N개 iteration이 모두 성공해야 완료된 continuation으로 처리합니다. 중간에 이미지 생성, 평가, 선택, 프롬프트 개선 또는 저장이 실패하면 발표 자료를 갱신하거나 자동으로 커밋·푸시하지 않습니다.

## 프로젝트 구조

```text
loop-practice/
├── AGENTS.md                    # 전체 루프 및 실행 규칙
├── README.md
├── main.py                      # run 탐색과 실행 계획 helper
├── config.py
├── requirements.txt
├── agents/
│   ├── generator.md             # 후보 생성 역할 지침
│   ├── evaluator.md             # 평가 및 선택 역할 지침
│   └── prompt_refiner.md         # 다음 프롬프트 개선 지침
├── docs/
│   ├── WORKFLOW.md              # 상세 워크플로
│   └── OUTPUT_FORMAT.md         # 결과 파일 및 JSON 형식
├── inputs/
│   └── pomeranian.png           # 고정 원본 사진
├── outputs/                     # 로컬 전체 실험 이력, Git 제외
│   └── run_YYYYMMDD_HHMMSS/
│       ├── summary.json
│       └── iteration_001/
│           ├── candidate_01.png
│           ├── candidate_02.png
│           ├── candidate_03.png
│           ├── selected.png
│           ├── prompt.txt
│           ├── evaluation.json
│           └── next_prompt.txt
├── scripts/
│   ├── build_presentation.py    # 최신 성공 run으로 발표 자료 생성
│   └── post_loop.py             # 발표 갱신, 검증, 커밋 및 푸시
├── src/                         # 역할별 Python 모듈 자리
└── presentation/
    ├── index.html
    ├── styles.css
    ├── script.js
    └── assets/latest-run/       # 배포에 필요한 최신 결과 자산
```

## `outputs/`와 다른 컴퓨터에서의 연속 실행

`outputs/`는 전체 실험 이력이 저장되는 로컬 전용 디렉터리이며 `.gitignore`에 포함되어 있습니다. 따라서 Git 커밋이나 GitHub 저장소에는 올라가지 않고, 저장소를 다른 컴퓨터에서 clone해도 자동으로 복원되지 않습니다.

기존 run을 다른 컴퓨터에서 이어서 실행하려면 원래 컴퓨터의 `outputs/` 디렉터리를 새 컴퓨터의 프로젝트 루트에 별도로 복사해야 합니다.

```text
원래 컴퓨터: loop-practice/outputs/
새 컴퓨터:   loop-practice/outputs/
```

`summary.json`, 모든 `iteration_...` 폴더, 후보 이미지, 평가 결과 및 `next_prompt.txt`가 함께 있어야 기존 run을 정상적으로 찾고 이어갈 수 있습니다. `outputs/`가 없으면 발표용 이미지가 저장소에 남아 있더라도 기존 run을 이어갈 수 없으며 새 run으로 시작합니다.

## 발표 자료 자동 갱신

요청한 추가 iteration이 모두 성공하면 전체 누적 run을 기준으로 `summary.json`을 다시 생성하고, 발표 자료를 정확히 한 번 갱신합니다.

`scripts/build_presentation.py`는 최신 성공 run을 읽어 `presentation/`을 재구성합니다. 발표에 실제로 필요한 결과 이미지만 `presentation/assets/latest-run/`에 복사하며, 로컬 실험 이력인 `outputs/` 전체를 발표 폴더로 복사하지 않습니다.

성공한 루프가 아니거나 일부 iteration만 완료된 경우에는 기존 발표 자료를 변경하지 않습니다.

## GitHub Pages 배포 흐름

성공한 루프의 후처리는 다음 순서로 진행됩니다.

```text
요청한 모든 iteration 완료
-> 누적 summary.json 갱신
-> presentation/ 한 번 재생성
-> Git 변경 및 민감정보 확인
-> 변경이 있으면 한 번 커밋
-> origin/main에 한 번 푸시
-> GitHub Actions가 presentation/을 GitHub Pages에 배포
```

기본 커밋 메시지는 다음과 같습니다.

```text
chore: update loop experiment results
```

GitHub Actions 설정은 `.github/workflows/deploy-pages.yml`에 있으며, `main` 브랜치에 푸시되면 `presentation/` 디렉터리를 GitHub Pages 아티팩트로 배포합니다.

## 관련 문서

- 전체 에이전트 규칙: `AGENTS.md`
- 상세 실행 흐름: `docs/WORKFLOW.md`
- 결과 파일과 JSON 형식: `docs/OUTPUT_FORMAT.md`
- 역할별 지침: `agents/`

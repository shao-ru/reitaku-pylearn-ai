# 教材コンテンツ形式 仕様書

版：v0.4（2026-10-21）

| 版 | 主な変更 |
| --- | --- |
| v0.4 | 知識グラフの再設計（`docs/knowledge_graph.md`）。単元（unit）と関係 `related` を追加。講義・練習ファイル・題単を単元に付けられるようにした。構造層（定型パターン）を専用トピック `pat` に分離。知識点 ID を教える順の連番に振り直し。`graph-doc` コマンド |
| v0.3 | 選択問題の「### 答えと解説」を「### 正解」と「### 解説」に分割。正解は記号だけを書く（`B`、`A, C`） |
| v0.2 | すべての問題の元を ipynb に統一（JSON は取り込み用の中間生成物）。問題 ID の自動付与（`assign-ids`）と ID・版番号の方針。問題形式は `choice` / `code` の2種類（バグ取り・穴埋めは `code`）。属性「タグ」。選択問題の複数正解。練習ファイル名に `_exNN`。JSON を元ファイル単位で出力し、JSON Schema を定義 |
| v0.1 | 初版 |

---

## 0. 基本方針

1. **すべての教材の「元」は ipynb / YAML とする。**
    - 教員が書く問題はもちろん、旧プラットフォームから移す問題や LLM で生成した問題も、ツールで ipynb に変換してから元として管理する。
    - 修正・レビュー・模範解答の実行は、すべて Jupyter 上の同じ手順で行える。
2. **JSON は取り込み用の中間生成物。** ツールが ipynb / YAML から生成する。手で編集せず、git にも入れない（`build/` に出力）。
    - LLM に問題を生成させるときは、検証しやすいように JSON で出力させ、ツールで ipynb に変換する。この JSON は生成の途中経過であり、元にはならない。
3. **1問の元は1か所だけ。** 同じ問題を2つのファイルで管理しない。

## 1. ファイルの種類

教材は次の **4種類のファイル** で管理する。どのファイルも知識点 ID（または単元 ID）で互いに結びつく。知識グラフの考え方（トピック・知識点・単元・層・関係）は **`docs/knowledge_graph.md`** を参照。

| 種類 | 形式 | 役割 | 行き先 |
| --- | --- | --- | --- |
| 知識グラフ定義 | YAML（1トピック1ファイル + `units.yaml`） | 知識点・層・難易度・知識点間の関係・単元 | AIサービスの知識グラフ |
| 講義ノート | ipynb | 説明 + 実行できるコード例 | そのまま LearnLab の教材 |
| 練習問題 | ipynb | 選択問題・コード問題（正解・模範解答・テスト付き） | 題庫（学生には直接見せない） |
| 題単 | YAML | 何を出題するか：静的な問題リスト、または動的選題の条件 | 出題・推薦モジュール |

```
graph.yaml, units.yaml ─┐
lessons/*.ipynb ────────┤   validate      export
exercises/*_exNN.ipynb ─┼──► 検証 ────────► build/json/（元ファイルごとの JSON）──► import ──► AIサービスの DB
sets/*.yaml ────────────┘                                                          （ID で更新／追加）
                         courseware
lessons/*.ipynb ─────────────────────────► build/courseware/ ──► LearnLab に教材として登録
```

**講義と練習を分ける理由**：講義ノートは学生が自由に実行する教材、練習問題は採点して習熟度を更新するためのもの。練習問題には正解・模範解答・テストケースなど学生に見せてはいけない情報が含まれるため、分けておけば講義ノートをそのまま LearnLab に載せられる。

---

## 2. ディレクトリ構成とファイル名

```
content/
├── units.yaml                       # トピックをまたぐ単元
├── templates/                       # テンプレート（単独で検証できる小さな例）
├── var/  io/  cond/  col/  func/    # 1トピック = 1フォルダ（文法層）
├── pat/                             # 定型パターン（構造層）
├── alg/  app/                       # アルゴリズム層・応用層
└── loop/
    ├── graph.yaml                   # 知識点・関係・このトピック内の単元
    ├── lessons/
    │   ├── loop_02_rangeと決まった回数の繰り返し.ipynb
    │   └── u_loop_for_for総合演習.ipynb                   # 単元に付けた講義
    ├── exercises/
    │   ├── loop_02_rangeと決まった回数の繰り返し_ex01.ipynb
    │   ├── loop_02_rangeと決まった回数の繰り返し_ex02.ipynb   # 同じ知識点の練習は複数ファイルに分けてよい
    │   └── u_loop_for_for総合演習_ex01.ipynb              # 単元の練習
    └── sets/
```

- 講義ノート：`<知識点ID>_<名前>.ipynb`、単元に付ける場合は `<単元ID>_<名前>.ipynb`
- 練習問題：`<知識点ID>_<名前>_exNN.ipynb`（NN = 01, 02, …）、単元の練習は `<単元ID>_<名前>_exNN.ipynb`
- 単元の教材は、単元を定義したトピックのフォルダに置く（`content/units.yaml` の単元なら、主に扱うトピックのフォルダ）。
- ツールはファイル名ではなく中身（メタデータセル）で種類を判定する。名前は人が探しやすくするための規則。
- `content/` 全体を検証するとき、`templates/` は対象外。

---

## 3. ID

### 3.1 付け方

- 使える文字：英数字・`_`・`-`（先頭は英数字）。**全ファイルを通して一意**。

| 対象 | 付け方 | 例 |
| --- | --- | --- |
| トピック | 英小文字の短い名前 | `loop`、`pat` |
| 知識点 | `トピック_連番`（手で付ける。最初は教える順。一度取り込んだら変えない。追加は最大の番号の次：`docs/authoring_guide.md` §3.3） | `loop_03` |
| 単元 | `u_名前`（トピック全体の単元は自動で作られ、ID = トピック名） | `u_loop_for` |
| 講義ノート | `lesson_知識点ID` / `lesson_単元ID` | `lesson_loop_03`、`lesson_u_loop_for` |
| 練習ファイル | `知識点ID_exNN` / `単元ID_exNN`（ファイル名と揃える） | `loop_02_ex02`、`u_loop_for_ex01` |
| 問題 | 連番 `<主知識点>_qNN`（選択）・`_cNN`（コード）、または `assign-ids` で自動付与 `<主知識点>-<6桁の16進>` | `loop_02_q05`、`pat_01-7a68a2` |
| 題単 | `set_名前` | `set_loop_quiz_basic` |

- 現在の教材の問題 ID は連番（v0.4 の移行時に振り直した）。新しく追加する問題は `assign-ids` で付けてよい（複数人が同時に追加しても衝突しない）。

### 3.2 問題 ID の自動付与（assign-ids）

1. 新しい問題は見出しを `## 問題` とだけ書く（ID を書かない）。
2. `uv run python -m tools.edu_content assign-ids content/` を実行する。
3. ID のない問題に ID が付き、**ipynb に書き戻される**。既存の ID は変わらない。何度実行しても同じ結果になる。
4. ID のない問題が残っていると `validate` はエラーになる（取り込めない）。

ID の後半は乱数なので、中央で番号を管理しなくても、複数人が別々のブランチで問題を追加して衝突しない。

### 3.3 ID の寿命

| 操作 | 扱い |
| --- | --- |
| 問題を修正した | **ID は変えない。** 再取り込みすると同じ問題として更新される |
| 修正で内容が変わった | JSON の `content_hash` が変わる。取り込み時に版番号を自動で上げ、解答記録には ID と版番号を保存する（修正前の記録も追跡できる） |
| 問題を元ファイルから削除した | 取り込み時に DB 上で「停止」にする（物理削除しない。解答記録が参照しているため）。停止した問題は出題しない |
| 問題を別ファイルに移した | ID が同じなら同じ問題として扱う |

> 取り込み（import）は AI サービスの DB 設計後に実装する。上の表はその方針。

---

## 4. ipynb のメタデータセル

講義ノートと練習問題の ipynb は、**最初のセル**を次のような markdown セルにする。

````markdown
```yaml
type: lesson        # lesson または exercises
id: lesson_loop_03
...
```
````

- `#` 以降は YAML のコメントとして無視される。
- LearnLab 用の教材を出力するとき、このセルは自動で削除される。

---

## 5. 知識グラフ定義（graph.yaml・units.yaml）

設計方針（層の判定基準、知識点の置き方、単元の使い方）は `docs/knowledge_graph.md`、現在の一覧は `docs/knowledge_graph_overview.md`（自動生成）。

```yaml
type: graph
topic: loop
title: 繰り返し

knowledge_points:
  - {id: loop_02, title: range と決まった回数の繰り返し, layer: 文法, difficulty: 2, keywords: [range(n)]}
  - {id: loop_03, title: range のステップ, layer: 文法, difficulty: 2}

relations:
  - {from: loop_02, to: loop_03, type: prerequisite}
  - {from: col_01, to: loop_01, type: prerequisite, note: 他トピックの知識点も指定できる}
  - {from: loop_02, to: col_03, type: related_error, weight: 0.8, note: range もスライスも終点を含まない}
  - {from: loop_04, to: var_07, type: related, note: 文字列の各文字へのアクセス}

units:                           # このトピックの一部を範囲とする単元（任意）
  - id: u_loop_for
    title: for文 総合演習
    knowledge_points: [loop_01, loop_02, pat_01, pat_02]
```

トピックをまたぐ単元は `content/units.yaml` に書く。

```yaml
type: units
units:
  - id: u_loop_col
    title: for文とコレクション
    topics: [loop, col]               # トピック単位で指定
    knowledge_points: [pat_04, pat_05] # 個別に追加
```

| 項目 | 必須 | 内容 |
| --- | --- | --- |
| `knowledge_points[].id` / `title` | ○ | 知識点 ID と表示名 |
| `layer` | ○ | `文法` / `構造` / `アルゴリズム` / `応用` |
| `difficulty` | ○ | 1〜9（1-3 初級、4-6 中級、7-9 上級） |
| `order` / `keywords` / `description` |  | 表示順・検索・説明 |
| `relations[].type` | ○ | `prerequisite`（from を習得してから to）/ `related_error`（混同しやすい）/ `related`（概念的な関連。順序に影響しない）/ `contains`（from が to を含む。現在未使用） |
| `relations[].weight` / `note` |  | 強さ 0.0〜1.0（省略時 1.0）／説明 |
| `units[].id` / `title` | ○ | 単元 ID（`u_` で始める）と表示名 |
| `units[].topics` / `knowledge_points` | どちらか ○ | 単元の範囲（両方書くと合わせた範囲） |

- 関係の `from` / `to` には他のトピックの知識点も指定できる。トピックをまたぐ関係は**後で学ぶ側**のトピックのファイルに書く。
- 各トピックには、トピック全体を範囲とする単元（ID = トピック名）が自動で作られる。
- エラー：ID の重複（知識点・単元・トピック名の間を含む）、存在しない知識点・トピックの参照、先修関係の循環。警告：どの関係にも出てこない知識点、同じ関係の重複。

---

## 6. 講義ノート（lessons/*.ipynb）

```yaml
type: lesson
id: lesson_loop_03
knowledge_points: [loop_03]     # この講義で扱う知識点（複数可）
# unit: u_loop_for              # 単元に付ける場合（総合演習のまとめなど）は knowledge_points の代わりに書く
```

- メタデータセルの後は自由に書く：説明、実行できるコード例、「やってみよう」のような**採点しない**小課題。
- **選択問題・正解（`### 正解`）・模範解答（`# @solution`）は書かない**（エラーになる）。

---

## 7. 練習問題（exercises/*_exNN.ipynb）

### 7.1 ファイル

```yaml
type: exercises
id: loop_02_ex02
title: range と決まった回数の繰り返し — 練習問題（2）
default_knowledge_point: loop_02    # 問題に「知識点」がないときの既定値（省略可）
# default_difficulty: 2             # 問題に「難易度」がないときの既定値（省略可）
# unit: u_loop_for                  # 単元の練習（総合演習など）の場合
```

- 通常は1つの知識点の練習ファイル（`default_knowledge_point` を書く）。問題によっては2番目以降に他の知識点を書いてよい。
- **単元の練習ファイル**（総合演習・単元テスト）は `unit` を書き、`default_knowledge_point` は書かない。問題ごとに `知識点` を書く。主知識点が単元の範囲外だと警告。
- `## 問題` 以外のセル（見出しや説明）は自由に置ける（取り込まれない）。

### 7.2 問題形式は2種類

| 形式 | 学生がすること | 判定 |
| --- | --- | --- |
| `choice`（選択問題） | 選択肢から選ぶ（1つまたは複数） | 正解の記号と比較 |
| `code`（コード問題） | プログラムを書いて提出する | テストケースを実行 |

**バグ取り・穴埋めは `code` に含める。** 画面も判定も同じで、違うのは初期コードと問題文だけ。

| 問題の作り | 初期コード（`@starter`） | 問題文に書くこと |
| --- | --- | --- |
| 通常のコーディング | 空、または入力の読み取りなど最低限 | 作るプログラムの仕様 |
| バグ取り | バグのあるプログラム | 何をするプログラムか、エラー出力や誤った出力 |
| 穴埋め | プログラムの一部（`pass  # ここを書き換える` など） | 完成させる部分 |

分類したい場合は属性「タグ」に `バグ取り`・`穴埋め` などと書く（表示・採点には影響しない）。

### 7.3 問題の書き方（共通）

1問 = `## 問題 <問題ID>` で始まる markdown セル（以下「見出しセル」）。新しい問題は `## 問題` だけでよい（3.2）。

````markdown
## 問題 pat_01_c02

- 形式: code
- 知識点: pat_01, loop_02
- 難易度: 3
- キーワード: `range(start, end)` `累積`
- タグ: 穴埋め

### 問題文
…

### ヒント
1. …
2. …
````

| 属性 | 必須 | 内容 |
| --- | --- | --- |
| `形式` |  | `choice`（省略時）/ `code` |
| `知識点` |  | 複数可。**先頭が主知識点**。省略時は `default_knowledge_point` |
| `難易度` |  | 1〜9。省略時は `default_difficulty`、それもなければ主知識点の難易度 |
| `キーワード` |  | 内容に関する語。`` `a` `b` `` または `a, b` |
| `タグ` |  | 分類用ラベル（`バグ取り`、`穴埋め`、`複数選択` など）。絞り込み・集計に使う |

| セクション | 必須 | 内容 |
| --- | --- | --- |
| `### 問題文` | ○ | 問題の本文（選択問題は選択肢も含む） |
| `### ヒント` |  | 番号付きリスト。段階的に見せる想定（答えそのものは書かない） |
| `### 正解` | 選択問題のみ ○ | 正解の記号だけ（7.4） |
| `### 解説` |  | 解答後に見せる説明。選択問題で空の場合は警告 |

正解（機械が判定に使う）と解説（学生が読む）を別のセクションにすることで、判定結果だけを先に返し、解説は後で見せる、といった使い分けもできる。

**複数の知識点を書く意味**：総合問題の正誤を、実際に関わる知識点すべての習熟度に反映するため。主知識点はグラフ上の所属・表示・出題範囲の判定に使う（例：二重ループで2次元リストの合計を求める問題 → `loop_08, pat_01`）。

### 7.4 選択問題（形式: choice）

````markdown
### 問題文

`0` / `1` / `2` を1行ずつ出力するコードを**すべて**選べ。

- A. `for i in range(3): print(i)`
- B. `for i in range(0, 3): print(i)`
- C. `for i in range(1, 3): print(i)`
- D.

    ```python
    for i in [0, 1, 2]:
        print(i)
    ```

### 正解

A, B, D

### 解説

`range(3)` と `range(0, 3)` はどちらも `0, 1, 2` を生成する。…
````

- 選択肢は `- A.` から順に 2〜6 個（A〜F）。複数行の選択肢は記号の下に**4文字字下げ**して書く（上の D）。
- `### 正解` には**選択肢の記号だけ**を書く：`B`、正解が複数なら `A, B, D`（区切りは `,` または `、`）。太字や説明文は書かない（エラーになる）。
- 複数正解の問題では、問題文に「すべて選べ」と明記する。

### 7.5 コード問題（形式: code）

見出しセルの後に3つのセルを続ける（順番は自由）。

| セル | 種類 | 1行目 | 内容 |
| --- | --- | --- | --- |
| 初期コード | code | `# @starter` | 学生に配るコード |
| 模範解答 | code | `# @solution` | 学生には見せない |
| テストケース | markdown | ` ```yaml ` の次の行が `# @tests` | 採点用のテスト |

見出しセルには選択問題と同じく `### 解説`（任意、解答後に見せる）を書ける。コード問題に `### 正解` はない（正解は模範解答とテストで表す）。

**テスト方式**

`mode: stdio` — 標準入力を与え、標準出力を比較する。

````markdown
```yaml
# @tests
mode: stdio
timeout: 2            # 1ケースの制限時間（秒、省略時 2）
cases:
  - input: |
      2
      5
    expected: |
      2
      3
      4
      5
    public: true      # 入出力例として学生に見せる
```
````

`mode: function` — コードを実行したあと `call` の式を評価し、戻り値を `expected` と `==` で比較する。

````markdown
```yaml
# @tests
mode: function
cases:
  - call: total(3)
    expected: 6
    public: true
```
````

- 現在の stdio の比較は文字列比較（行末の空白と最後の空行のみ無視）。実数の誤差許容などは今後追加する（`docs/todo.md`）。
- `public: true` のケースが1つもないと警告。

### 7.6 検証ツールのチェック

| 対象 | エラーになる条件 |
| --- | --- |
| 全体 | ID がない・重複、存在しない知識点・問題の参照 |
| 選択問題 | 選択肢が2つ未満、記号が A から連続していない、`### 正解` がない・記号以外が書いてある・選択肢にない・重複、旧形式の `### 答えと解説` |
| コード問題 | @starter / @solution / @tests のいずれかがない |
| コード問題 | **模範解答がテストに1つでも失敗する** |
| コード問題 | **初期コードのままで全テストに通る**（テストが甘い。バグ取りなら「バグが再現しない」） |

旧プラットフォームから移した問題や LLM で生成した問題も、ipynb に変換したあと同じチェックを通す。

> 検証ツールのテスト実行は、教員が書いたコードを確認するためのもので、サンドボックスではない。学生の提出コードは M4 の採点サンドボックスで実行する。

---

## 8. 題単（sets/*.yaml）

### 静的（mode: static）

```yaml
type: set
id: set_loop_quiz_basic
title: for文 基礎 小テスト
mode: static
shuffle: false
items: [loop_01_q01, loop_02_q02, loop_02_c01]
```

### 動的選題（mode: adaptive）

```yaml
type: set
id: set_loop_practice_adaptive
title: for文 おまかせ練習
mode: adaptive
selection:
  units: [u_loop_for]               # 単元で範囲を指定
  # knowledge_points: [loop_01, loop_02]   # 知識点で指定
  # topics: [loop]                         # トピックで指定
  difficulty: [1, 5]
  question_types: [choice, code]
  count: 10
  recommender: MyRecommender
```

- 範囲は `units`・`knowledge_points`・`topics` を組み合わせて指定できる（合わせた範囲）。
- 候補は「主知識点が範囲内（または指定した単元の練習ファイルの問題）」「難易度が範囲内」「形式が一致」する問題。候補が `count` より少ないと警告。
- 出題するのは**題庫に登録済みの問題だけ**。その場で LLM に問題を作らせることはしない。

---

## 9. JSON 出力

`export` は元ファイル1つにつき JSON ファイル1つを、元と同じ相対パスで出力する。

```
build/json/units.json
build/json/loop/graph.json                     # 知識点・関係・このトピック内の単元（範囲を展開した members 付き）
build/json/loop/lessons/loop_02_rangeと決まった回数の繰り返し.json
build/json/loop/exercises/loop_02_rangeと決まった回数の繰り返し_ex02.json
build/json/loop/sets/loop_quiz_basic.json
```

練習問題の JSON の形式は **`docs/schema/exercises.schema.json`**（JSON Schema）で定義する。1問の例：

```json
{
  "id": "loop_02_c03",
  "question_type": "code",
  "knowledge_points": ["loop_02", "io_03"],
  "primary_knowledge_point": "loop_02",
  "unit": null,
  "difficulty": 2,
  "keywords": ["range(n)", "input", "int"],
  "tags": ["バグ取り"],
  "hints": ["エラーメッセージは…", "input() が返す値の型は何か。"],
  "question": "整数 n を入力として受け取り…",
  "explanation": "input() は常に文字列を返す。…",
  "starter_code": "n = input()\nfor i in range(n):\n    print(i)\n",
  "solution_code": "n = int(input())\nfor i in range(n):\n    print(i)\n",
  "tests": {"mode": "stdio", "timeout": 2,
            "cases": [{"input": "3", "expected": "0\n1\n2\n", "public": true}]},
  "content_hash": "70a49e021cb39bfd"
}
```

- 選択問題は `options`（選択肢の配列）と `correct_answers`（正解の記号の配列。単一正解でも配列）を持つ。
- `unit` は単元の練習ファイルの問題なら単元 ID、それ以外は `null`。
- `content_hash` は ID と元ファイルの場所を除いた内容から計算する。内容が同じなら何度出力しても同じ値になる。

---

## 10. ツール

リポジトリのルートで実行する。Python とパッケージは uv で管理する（Python 3.12、依存は `pyproject.toml`）。初回だけ `uv sync` を実行して環境を作る。

| コマンド | 内容 |
| --- | --- |
| `uv run python -m tools.edu_content validate content/` | 検証（エラーがあれば終了コード 1）。`--no-run` でコード問題の実行を省略 |
| `uv run python -m tools.edu_content assign-ids content/` | ID のない問題に ID を付けて ipynb に書き戻す。`--dry-run` で確認だけ |
| `uv run python -m tools.edu_content export content/ -o build/json/` | 元ファイルごとの JSON を出力（エラーがあれば出力しない） |
| `uv run python -m tools.edu_content courseware content/ -o build/courseware/` | メタデータセルを除いた講義ノートを出力（LearnLab 用） |
| `uv run python -m tools.edu_content graph-doc content/ -o docs/knowledge_graph_overview.md` | 知識グラフの一覧（知識点・単元・関係・教材の数）を Markdown で生成 |
| `import` | JSON を AI サービスの DB に取り込む（ID で更新／追加、版番号、停止）。**未実装**（DB 設計後） |

テンプレートだけを検証する場合は `validate content/templates/`。

**問題・知識点・トピック・単元・題単を追加する手順**は `docs/authoring_guide.md` を参照（要点：書く → `assign-ids` → `validate` → グラフを変えたら `graph-doc` → コミット・PR）。

---

## 11. 移行メモ

### v0.4：知識グラフの再設計（2026-10-21）

- 知識グラフを 9 トピック（var・io・cond・col・loop・func・pat・alg・app）、知識点 62 個に作り直した。設計方針は `docs/knowledge_graph.md`。
- `loop` は文法層だけにし、知識点 ID を教える順の連番に振り直した（`loop_01`〜`loop_11`）。
    - 旧 `loop_01` と旧 `loop_02`（繰り返しが必要な理由）を統合 → `loop_01`
    - 旧 `loop_03`（range）と旧 `loop_04` の「決まった回数の繰り返し」→ `loop_02`
    - 旧 `loop_04` の累積、旧 `loop_07` の平均 → `pat_01`。旧 `loop_07` の最大・最小 → `pat_03`。旧 `loop_05`（リスト作成）→ `pat_04`・`pat_05`
    - 旧 `loop_06`（辞書と for）→ `loop_05`、旧 `loop_08`〜`10` → `loop_08`〜`10`、旧 `loop_12`（while）→ `loop_11`
    - 旧 `loop_13`（for文 総合演習）は知識点ではなく単元 `u_loop_for` にした
    - 新規：`loop_03`（range のステップ）、`loop_04`（文字列のループ）、`loop_06`（enumerate）、`loop_07`（zip）
- 問題 124 問の ID を新しい知識点に合わせて振り直し、知識点を付け直した（主知識点 + 使っている他の知識点）。旧 ID との対応は `docs/migration/id_mapping_v04.csv`。
    - 問題文・選択肢・正解・解説・コード・テストは変更していない（移行前後の出力 JSON を全問比較して確認済み）。旧クラシック形式の名残だった問題文先頭の `**問題N.**`（89問）だけ削除した。
    - 講義ノートの本文も、旧ファイルの全行が新しい講義ノートに含まれていることを確認済み。
- 新規の知識点 4 つの講義ノートと練習問題（各 4〜5問）は Claude が作成した下書き。メタデータに「下書き」、問題にタグ `AI作成` を付けている。教員のレビューが必要。

### v0.1〜v0.3：semi-edu-ai からの移行

- `semi-edu-ai/knowledge/beginner_loop/` の12ファイルを講義ノートと練習問題に分けて変換した（元のファイルは変更していない）。選択問題 118 問は、元の取り込み結果と一致することを確認済み。
- v0.3 で全選択問題を「### 正解」「### 解説」形式に変換した。

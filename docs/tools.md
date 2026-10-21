# 教材ツール（tools/edu_content）の実装

版：v1.0（2026-10-21）

教材ファイル（YAML・ipynb）を読み込んで検証し、AI サービスが取り込む JSON や LearnLab 用の教材を出力するツールの内部構成をまとめる。ツールを修正・拡張する人向け。使い方だけなら `README.md` と `docs/authoring_guide.md` で足りる。

---

## 1. 全体の流れ

```
content/**/graph.yaml ─┐
content/units.yaml ────┤
content/**/*.ipynb ────┼─► load_all() ─► check_all() ─┬─► Report（エラー・警告）……… validate
content/**/sets/*.yaml ┘   読み込み・解析   相互参照の検証  ├─► write_json() ─► build/json/ … export
                                            コードの実行   └─► render() ─► overview.md … graph-doc
content/**/lessons/*.ipynb ─► write_courseware() ─► build/courseware/ ……… courseware
content/**/exercises/*.ipynb ─► assign_ids() ─► 同じ ipynb に ID を書き戻す ……… assign-ids
```

- **読み込み（load）と検証（check）を分けている。** 各ファイルの解析で分かる誤り（書式・必須項目）は読み込み時に、ファイルをまたぐ誤り（存在しない知識点の参照、ID の重複、循環）は `check_all` で検出する。
- **エラーは例外で止めず、`Report` にすべて集めてから表示する。** 1回の実行ですべての問題が分かるようにするため。
- **ツールは DB に触れない。** 出力は JSON まで。DB への取り込み（import）は AI サービス側で行う（未実装）。

---

## 2. モジュール構成

| ファイル | 役割 | 主な関数 |
| --- | --- | --- |
| `__main__.py` | コマンドライン（`validate` / `assign-ids` / `export` / `courseware` / `graph-doc`） | `main()` |
| `common.py` | 共通部品：エラー収集、ipynb の読み込み、メタデータセルの検出、YAML ブロックの解析、定数（層・関係の種類・ID の形式） | `Report`、`find_meta_cell()`、`split_list()` |
| `graph.py` | `graph.yaml`・`units.yaml` の読み込みと、グラフ全体の検証（ID の重複、関係の参照先、先修関係の循環、単元の範囲の展開） | `load_graph()`、`load_units_file()`、`check_graphs()` |
| `lesson.py` | 講義ノートの解析（知識点または単元、本文の markdown 化、正解の混入チェック）と LearnLab 用の出力 | `load_lesson()`、`write_courseware()` |
| `exercise.py` | 練習問題の解析：`## 問題` の見出しセル、属性、`###` セクション、選択肢、`@starter`・`@solution`・`@tests` のセル | `load_exercises()` |
| `runner.py` | コード問題のテスト実行（stdio / function）。教員が書いたコードの確認用で、サンドボックスではない | `run_tests()` |
| `content.py` | すべてのファイルの読み込み、相互参照の検証、コード問題の実行、題単の候補数の計算、JSON 出力、`content_hash` | `load_all()`、`check_all()`、`write_json()` |
| `ids.py` | `assign-ids`：ID のない問題に `<主知識点>-<6桁の16進>` を付けて書き戻す | `assign_ids()` |
| `graphdoc.py` | `graph-doc`：知識グラフの一覧（Markdown・mermaid）を生成 | `render()`、`content_counts()` |

ファイルの種類は**拡張子とメタデータで判定**する（ファイル名やフォルダ名には依存しない）。

| 拡張子 | 判定 | 処理 |
| --- | --- | --- |
| `.yaml` | `type: graph` | `graph.load_graph` |
| `.yaml` | `type: units` | `graph.load_units_file` |
| `.yaml` | `type: set` | `content._load_set` |
| `.ipynb` | 最初のセルの ```` ```yaml ```` に `type: lesson` | `lesson.load_lesson` |
| `.ipynb` | 同 `type: exercises` | `exercise.load_exercises` |

`templates/`、`.` で始まるフォルダ、`.ipynb_checkpoints` は `content/` 全体の検証では読み飛ばす（`content._skip`）。

---

## 3. 設計の概念とファイル・データの対応

`docs/knowledge_graph.md` の概念が、どのファイルのどこに書かれ、出力 JSON のどこに出るか。

| 概念 | 書く場所 | 出力 JSON | 主なキー |
| --- | --- | --- | --- |
| トピック | フォルダ + `graph.yaml` の `topic`・`title` | `<トピック>/graph.json` | `topic`、`title` |
| 知識点 | `graph.yaml` の `knowledge_points` | `graph.json` の `knowledge_points[]` | `id`、`topic`、`title`、`layer`、`difficulty`、`keywords`、`description`、`order` |
| 関係 | `graph.yaml` の `relations` | `graph.json` の `relations[]` | `from_id`、`to_id`、`relation_type`、`weight`、`note` |
| 単元（トピック内） | `graph.yaml` の `units` | `graph.json` の `units[]` | `id`、`title`、`topics`、`knowledge_points`、**`members`**（展開後の全知識点）、`defined_in` |
| 単元（トピックをまたぐ） | `content/units.yaml` | `units.json` の `units[]` | 同上 |
| 単元（トピック全体） | 書かない（自動） | `export` の JSON には出ない（`check_all` の戻り値と `graph-doc` にだけ出る） | `auto: true` |
| 講義ノート | `lessons/*.ipynb` | `lessons/<名前>.json` | `id`、`title`、`knowledge_points` または `unit`、`content`（markdown） |
| 練習ファイル | `exercises/*.ipynb` のメタデータ | `exercises/<名前>.json` | `id`、`title`、`exercises[]` |
| 問題 | `## 問題` のセル（+ コード問題の3セル） | `exercises[]` の各要素 | `docs/schema/exercises.schema.json`（§4） |
| 題単 | `sets/*.yaml` | `sets/<名前>.json` | `id`、`mode`、`items`、`selection`、`shuffle`、`pool_size`（adaptive のみ） |

すべての JSON には `type`（`graph` / `units` / `lesson` / `exercises` / `set`）と `source`（元ファイルの相対パス）が付く。JSON は元ファイルと同じ相対パスに出力される（`content/loop/graph.yaml` → `build/json/loop/graph.json`）。

---

## 4. 問題の JSON

形式は `docs/schema/exercises.schema.json`（JSON Schema 2020-12）で定義している。取り込み側はこのスキーマで検証してから DB に入れる。

| キー | 選択 | コード | 内容 |
| --- | --- | --- | --- |
| `id` | ○ | ○ | 問題 ID |
| `question_type` | `choice` | `code` | ipynb の「形式」 |
| `knowledge_points` | ○ | ○ | 知識点（先頭が主） |
| `primary_knowledge_point` | ○ | ○ | `knowledge_points[0]` |
| `unit` | ○ | ○ | 単元の練習ファイルなら単元 ID、それ以外は `null` |
| `difficulty` | ○ | ○ | 属性 → `default_difficulty` → 主知識点の難易度 の順に決まる |
| `keywords`・`tags`・`hints` | ○ | ○ | 文字列の配列 |
| `question` | ○ | ○ | 問題文（選択問題は選択肢を除いた部分） |
| `explanation` | ○ | ○ | 解説（なければ `null`） |
| `options` | ○ | | 選択肢の配列（記号は含まない） |
| `correct_answers` | ○ | | 正解の記号の配列（例：`["A", "C"]`） |
| `starter_code`・`solution_code` | | ○ | 初期コード・模範解答（1行目のマーカーは除く） |
| `tests` | | ○ | `{mode, timeout, cases[]}`。`cases` は stdio なら `input`・`expected`、function なら `call`・`expected`、どちらも `public` |
| `content_hash` | ○ | ○ | `id` と `source` を除いた内容の SHA-256 の先頭16桁。取り込み時に変更を検出して版番号を上げるのに使う |

---

## 5. 主な処理の詳細

### 5.1 練習問題の解析（exercise.py）

1. 最初のセル（メタデータ）から `id`・`default_knowledge_point`・`default_difficulty`・`unit` を読む。
2. `## 問題 <ID>`（ID 省略可）で始まる markdown セルを探す（`QUESTION_HEAD_RE`）。次の見出しセルまでが1問。
3. 見出しの直後の `- 属性: 値` を読む（`ATTR_RE`：形式・知識点・難易度・キーワード・タグ）。
4. `### 見出し` でセクションに分ける（`_sections`）。問題文・ヒント・正解・解説。
5. 選択問題：問題文から `- A. …` を選択肢として切り出す（`_parse_options`。字下げされた複数行も可）。`### 正解` は記号だけ（`ANSWER_RE`）。
6. コード問題：見出しセルの後のセルのうち、1行目が `# @starter` / `# @solution` の code セルと、` ```yaml ` の次の行が `# @tests` の markdown セルを集める（`_block_kind`）。

### 5.2 コード問題の実行（runner.py）

- `stdio`：模範解答を `python -I` の別プロセスで実行し、`input` を標準入力に渡して標準出力を比較する。比較は行末の空白と最後の空行を無視した文字列比較（`normalize_output`）。
- `function`：ハーネス（`_FUNCTION_HARNESS`）がコードを `exec` し、`call` を `eval` して `expected` と `==` で比較する。
- 文字コードは UTF-8 に固定（Windows の cp932 対策）。タイムアウトは1ケース `timeout` 秒（既定 2）。
- `check_all` は、**模範解答が全ケースに通ること**と、**初期コードが全ケースには通らないこと**を確かめる。`--no-run` で省略できる。

### 5.3 グラフの検証（graph.py）

- 知識点 ID・トピック名・単元 ID がすべての間で重複しないこと。
- 関係の両端が存在すること、自分自身への関係でないこと。同じ関係の重複は警告（`related` は向きを区別しない）。
- 先修関係（`prerequisite`）だけで深さ優先探索し、循環を検出する。
- 単元の範囲（`topics` + `knowledge_points`）を展開して `members` を作る。トピックごとの単元を自動で追加する。

### 5.4 ID の付与（ids.py）

- 全練習ファイルの既存の問題 ID を集め、重複しない `<主知識点>-<secrets.token_hex(3)>` を作る。
- 見出し行だけを書き換えて ipynb を保存する（他のセルは変更しない）。既存の ID は変えないので、何度実行しても結果は同じ。

---

## 6. 拡張するときの手順

| やりたいこと | 変更する場所 |
| --- | --- |
| 問題に属性を追加（例：「目標時間」） | `exercise.py` の `ATTR_RE` と `ex` 辞書の組み立て → `docs/schema/exercises.schema.json` → `docs/content_format.md` §7.3 → テンプレート |
| 問題の形式を追加（例：`fill_blank`） | `exercise.py` の `TYPES` と解析の分岐 → スキーマの `question_type` と `allOf` の条件 → 仕様書 §7 → 必要なら `runner.py` |
| テストの方式を追加（例：実数の誤差許容） | `exercise.py` の `_parse_tests`（新しいキーの読み込み）→ `runner.py`（比較方法）→ スキーマの `tests` → 仕様書 §7.5 |
| 関係の種類を追加 | `common.py` の `RELATION_TYPES`（向きがなければ `graph.py` の `UNDIRECTED` にも）→ `graphdoc.py` の `REL_LABEL` → `docs/knowledge_graph.md` §4 |
| 検証ルールを追加 | ファイル単体で分かるものは各 `load_*`、ファイルをまたぐものは `content.check_all` または `graph.check_graphs` に `report.error()` / `report.warn()` を追加 → `docs/authoring_guide.md` §9 のエラー表 |
| 出力 JSON にキーを追加 | 各 `load_*` が返す辞書に追加すれば `write_json` がそのまま出力する。`_` で始まるキーは出力されない（内部用） |
| コマンドを追加 | `__main__.py` の `sub.add_parser` と処理 → `README.md`・仕様書 §10 |

**守ること**

- エラーメッセージは日本語で、**何が問題で、どう直すか**が分かるように書く（例：`問題 ID がありません（… assign-ids で付与できます）`）。
- 取り込みを止めるべき誤りは `error`、教材として成立するが確認してほしいものは `warn`。
- ツールは教材ファイルを書き換えない（例外は `assign-ids` の見出し行だけ）。
- 仕様（`docs/content_format.md`）・スキーマ・テンプレート・この文書を同じ PR で更新する。

---

## 7. 動作確認

自動テスト（pytest）はまだない（`docs/todo.md`）。変更したら少なくとも次を確認する。

```powershell
uv run python -m tools.edu_content validate content/             # エラー 0 件
uv run python -m tools.edu_content validate content/templates/   # エラー 0 件
uv run python -m tools.edu_content export content/ -o build/json/
uv run python -m tools.edu_content graph-doc content/ -o docs/knowledge_graph_overview.md
```

検証ルールを追加・変更したときは、`content/` をコピーした作業用フォルダに**わざと誤りを入れて**、エラーが出ることも確かめる（例：存在しない知識点を書く、正解を選択肢にない記号にする、模範解答を壊す）。

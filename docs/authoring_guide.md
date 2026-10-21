# 教材の作成・追加ガイド

版：v1.1（2026-10-21）

この文書は、知識点・講義ノート・練習問題・単元・題単を**新しく作る／追加する**ときの手順書である。ゼミのメンバーが同じ手順で作業できるように、作業の種類ごとに手順と注意点をまとめる。

| 知りたいこと | 文書 |
| --- | --- |
| なぜこういう構成なのか（層・トピック・単元・関係の考え方） | `docs/knowledge_graph.md` |
| ファイルの書き方の細かい規則（属性・セクション・テスト形式） | `docs/content_format.md` |
| いまある知識点・単元の一覧 | `docs/knowledge_graph_overview.md`（自動生成） |
| ツールの中身を変更・拡張したい | `docs/tools.md` |
| **何かを作る・追加する手順** | **この文書** |

---

## 0. はじめに（初回だけ）

**必要なもの**：GitHub アカウント、[Git](https://git-scm.com/)、[uv](https://docs.astral.sh/uv/)。リポジトリへの書き込み権限は教員が招待する（GitHub から届く招待メールを承認する）。

```powershell
git clone https://github.com/shao-ru/reitaku-pylearn-ai.git
cd reitaku-pylearn-ai
uv sync                           # Python 3.12 と依存パッケージを入れる
uv run python -m tools.edu_content validate content/
```

最後のコマンドで `エラー 0 件` と出れば準備完了。ipynb は Jupyter（JupyterLab）または VS Code で編集する。

**コミットに使う名前とメールアドレス**：公開リポジトリなので、コミットに記録されるメールアドレスは誰でも見られる。大学や個人のアドレスではなく、GitHub の非公開用アドレスを設定する（GitHub → Settings → Emails の「Keep my email addresses private」を有効にすると表示される `数字+ユーザー名@users.noreply.github.com`）。

```powershell
git config user.name  "GitHub のユーザー名"
git config user.email "数字+ユーザー名@users.noreply.github.com"
```

`--global` を付けなければ、このリポジトリだけの設定になる。

---

## 1. すべての作業に共通する流れ

```
① ブランチを作る → ② ファイルを書く → ③ assign-ids → ④ validate → ⑤ graph-doc（グラフを変えたとき）→ ⑥ コミット・PR
```

```powershell
git switch -c feature/<名前>-<作業内容>          # 例：feature/yamada-pat07-exercises
# … ファイルを編集 …
uv run python -m tools.edu_content assign-ids content/   # 新しい問題に ID を付ける
uv run python -m tools.edu_content validate content/     # エラー 0 件になるまで直す
uv run python -m tools.edu_content graph-doc content/ -o docs/knowledge_graph_overview.md   # グラフ・単元を変えたとき
git add content/ docs/
git commit -m "feat: pat_07 の練習問題を追加"
git push -u origin feature/<名前>-<作業内容>
```

### PR を出す前のチェックリスト

- [ ] `validate` が **エラー 0 件**（警告は内容を確認し、意図したものなら PR に理由を書く）
- [ ] 新しい問題に ID が付いている（`assign-ids` 済み）
- [ ] グラフ（`graph.yaml`・`units.yaml`）を変えた場合、`graph-doc` で一覧を更新した
- [ ] `build/`・`.venv/` をコミットしていない（`.gitignore` 済み）
- [ ] コミットのメールアドレスが noreply アドレスになっている（`git log -1 --format=%ae` で確認）
- [ ] 練習問題の ipynb は出力をクリアした（Jupyter の「Clear All Outputs」。差分が小さくなる）
- [ ] 他の人の担当ファイルを書き換えていない（§8）

---

## 2. 既存の知識点に練習問題を追加する

もっとも多い作業。**他の人のファイルに追記するより、新しい練習ファイル（`_exNN` の次の番号）を作る方が衝突しない。**

1. テンプレートをコピーする：`content/templates/exercise_template.ipynb` → `content/<トピック>/exercises/<知識点ID>_<名前>_exNN.ipynb`
    - 例：`content/pat/exercises/pat_03_最大値と最小値_ex02.ipynb`
2. 先頭のメタデータセルを書き換える。

    ````markdown
    ```yaml
    type: exercises
    id: pat_03_ex02                     # ファイル名と揃える
    title: 最大値・最小値の更新 — 練習問題（2）
    default_knowledge_point: pat_03
    ```
    ````

3. テンプレートの説明セルと例の問題を消し、問題を書く。**見出しは `## 問題` だけでよい**（ID は手順 4 で付く）。

    ````markdown
    ## 問題

    - 形式: choice
    - 難易度: 3
    - キーワード: `最大値` `初期化`
    - タグ: バグ取り

    ### 問題文

    次のコードはリストの最大値を求めるつもりだが、`[-5, -2, -9]` に対して誤った結果を出す。原因として正しいものはどれか？

    ```python
    max_val = 0
    for n in [-5, -2, -9]:
        if n > max_val:
            max_val = n
    print(max_val)
    ```

    - A. `if` の条件が逆
    - B. `max_val` の初期値が 0 なので、負の数しかないときに更新されない
    - C. `print` の位置がループの中にない
    - D. `for` で回す対象が間違っている

    ### 正解

    B

    ### 解説

    初期値は 0 ではなく最初の要素（`nums[0]`）にする。
    ````

4. `assign-ids` → `validate`。

### 問題を書くときの注意

- **1問 = 1つの markdown セル**（コード問題はその後に `@starter`・`@solution`・`@tests` のセルが続く）。
- **知識点**：その問題で主に練習させる知識点を先頭に書く。他の知識点も使っているなら2番目以降に追加する（例：`- 知識点: pat_03, loop_05`）。省略すると `default_knowledge_point` になる。
- **難易度**：知識点の難易度を目安に 1〜9。
- **選択肢**：誤答には「よくある誤解」を入れる（範囲の終点を含めてしまう、初期化の位置を間違える、など）。誤答の理由を解説に書く。
- **複数正解**：問題文に「すべて選べ」と書き、`### 正解` に `A, C` のように書く。
- **問題文の番号**（「問題1.」など）は書かない。並べ替えると番号がずれる。

### コード問題の注意

- `@starter`（学生に配るコード）、`@solution`（模範解答）、`@tests`（テスト）の3セルが必要。書き方の例は `content/templates/exercise_template.ipynb` と `content/loop/exercises/loop_02_…_ex02.ipynb`。
- `validate` は**模範解答が全テストに通ること**と、**初期コードのままでは通らないこと**を実際に実行して確かめる。
- バグ取り：`@starter` にバグのあるプログラムを置き、問題文にエラー出力などを書く。穴埋め：`@starter` にプログラムの一部（`pass  # ここを書き換える` など）を書く。
- テストケースは**境界の値**（0、1、空のリスト、負の数）を入れる。1つは `public: true` にして入出力例として見せる。
- **実数を出力する問題は避けるか、出力を整える**（`round` や f 文字列で桁数を決める）。現在の判定は文字列比較なので、`0.1 + 0.2` のような誤差で正しい答えが不正解になる（実数の誤差許容は今後対応：`docs/todo.md`）。
- 関数を書かせる問題は `mode: function`（`call: total(3)` と戻り値で判定）。

---

## 3. 知識点を追加する

### 3.1 まず確認すること

- **本当に新しい知識点か？** 既存の知識点の練習問題で済むなら、問題を追加する（§2）。
- **どの層か？** `docs/knowledge_graph.md` §2 の判定基準で決める。1つの言語機能なら文法層、名前の付く定番の書き方なら構造層（`pat`）。
- **組み合わせの練習なら単元**（§5）。新しい知識を含まないものは知識点にしない。
- **どのトピックに置くか？** 最初に教える場所。迷ったら PR で相談する。

### 3.2 手順

1. `content/<トピック>/graph.yaml` の `knowledge_points` に追加する。

    ```yaml
      - {id: loop_12, title: for-else, layer: 文法, difficulty: 4, keywords: [for, else, break]}
    ```

    - **ID は、そのトピックで使われている最大の番号の次**（`loop_11` まであれば `loop_12`）。教える順の途中に入る知識点でも、既存の ID は振り直さない（§3.3）。
    - **表示順は YAML の並び順**。教える順の位置にこの行を挿入すればよい（`order` を書けばそちらが優先）。
2. 同じファイルの `relations` に**先修関係**を書く。少なくとも1つ（前提となる知識点 → 新しい知識点）。混同しやすい知識点があれば `related_error`、概念的な関連は `related`。

    ```yaml
      - {from: loop_09, to: loop_12, type: prerequisite, note: break を使うときの else}
    ```

    - 他トピックの知識点が前提なら、それも書いてよい（トピックをまたぐ関係は**後で学ぶ側**＝このファイルに書く）。
3. 講義ノートを作る：`content/templates/lesson_template.ipynb` → `content/<トピック>/lessons/<知識点ID>_<名前>.ipynb`。メタデータは `id: lesson_<知識点ID>`、`knowledge_points: [<知識点ID>]`。
4. 練習問題を作る（§2）。ファイル名は `<知識点ID>_<名前>_ex01.ipynb`。
5. 単元の範囲に入れるべきなら、単元の `knowledge_points` に追加する（例：for 文の知識点なら `loop/graph.yaml` の `u_loop_for`）。
6. `validate` → `graph-doc`。

### 3.3 知識点 ID のルール

| 場面 | ルール |
| --- | --- |
| 新しいトピックを作るとき | 教える順に `_01` から連番を振る |
| 既存のトピックに追加するとき | 最大の番号の次を使う。表示順は YAML の並び順（または `order`）で決める |
| 知識点の名前・説明・難易度を直すとき | ID はそのまま |
| 知識点を分割・統合するとき | 問題の付け替えが必要になるので、PR で相談してから行う |

一度取り込んだ知識点の ID を変えると、解答記録・習熟度との対応が切れる。番号が教える順と多少ずれても、ID は変えない。

---

## 4. トピックを追加する

例：「文字列の詳細」を `str` トピックとして追加する。

1. フォルダを作る：`content/str/`（`lessons/`・`exercises/` はファイルを置くときに作る）。
2. `content/templates/graph_template.yaml` を `content/str/graph.yaml` にコピーし、`topic: str`、`title: 文字列` にする。
3. 知識点を教える順に `str_01`、`str_02`、… と書く。
4. 先修関係を書く。**他のトピックからの先修関係（例：`var_03 → str_01`）はこのファイルに書く。**
5. 講義ノート・練習問題を作る（§3.2 の 3〜4）。
6. トピック全体の単元（ID = `str`）は自動で作られる。前半まとめなどに含めるなら `content/units.yaml` の該当単元の `topics` に `str` を追加する。
7. `validate` → `graph-doc`。

トピック名は英小文字の短い名前にする（知識点 ID の接頭辞になる）。

---

## 5. 単元と総合演習を作る

### 5.1 単元を定義する

| 範囲 | 書く場所 | 例 |
| --- | --- | --- |
| 1つのトピックの一部 | そのトピックの `graph.yaml` の `units` | `u_loop_for` |
| トピックをまたぐ | `content/units.yaml` | `u_loop_col`、`u_midterm` |
| 1つのトピック全体 | 書かない（自動で作られる。ID = トピック名） | `loop` |

```yaml
units:
  - id: u_func_pat                 # u_ で始める
    title: 関数で書くパターン
    topics: [func]                 # トピック単位の範囲（任意）
    knowledge_points: [pat_01, pat_03]   # 個別に追加（任意）
```

### 5.2 総合演習（単元の講義・練習）を作る

例：単元 `u_loop_col` の総合演習。

1. 講義ノート（まとめ）：`content/loop/lessons/u_loop_col_forとコレクション.ipynb`

    ````markdown
    ```yaml
    type: lesson
    id: lesson_u_loop_col
    unit: u_loop_col          # knowledge_points の代わりに unit を書く
    ```
    ````

2. 練習ファイル：`content/loop/exercises/u_loop_col_forとコレクション_ex01.ipynb`

    ````markdown
    ```yaml
    type: exercises
    id: u_loop_col_ex01
    title: for文とコレクション — 総合演習
    unit: u_loop_col          # default_knowledge_point は書かない
    ```
    ````

3. **各問題に「知識点」を必ず書く**。先頭（主知識点）は単元の範囲内の知識点にする（範囲外だと警告）。2番目以降は前提になる他の知識点でもよい。

    ```markdown
    - 形式: choice
    - 知識点: pat_07, col_07, var_08
    ```

4. 単元の教材は、単元を定義したトピックのフォルダに置く（`units.yaml` の単元なら、主に扱うトピックのフォルダ）。

---

## 6. 題単を作る

`content/<トピック>/sets/<名前>.yaml`。テンプレートは `content/templates/set_template_static.yaml`・`set_template_adaptive.yaml`。

```yaml
# 小テスト（全員同じ問題）
type: set
id: set_pat_quiz_01
title: パターン 小テスト①
mode: static
items: [pat_01_q01, pat_03_q02, pat_01_c01]
```

```yaml
# 日常練習（推薦アルゴリズムが選ぶ）
type: set
id: set_pat_practice
title: パターン おまかせ練習
mode: adaptive
selection:
  topics: [pat]
  difficulty: [2, 4]
  count: 10
  recommender: MyRecommender
```

問題 ID は `docs/knowledge_graph_overview.md` ではなく練習ファイルで確認する。`export` の出力（`build/json/…`）を見てもよい。

---

## 7. Claude（LLM）が作った下書きをレビューする

LLM が作った講義・問題には次の印が付いている。

- 講義・練習ファイルのメタデータに `# 下書き：Claude が作成（教員レビュー前）`
- 問題の属性に `- タグ: AI作成`

レビューの手順：

1. 内容を確認する：正解・解説の正しさ、まだ習っていない文法を使っていないか、難易度、日本語の表現。
2. コード問題は `validate` が実行して確かめるが、**選択問題の正解はツールでは確かめられない**。コードを Jupyter で実際に実行して確認する。
3. 直したら、メタデータの「下書き」の行を削除する。問題のタグ `AI作成` は残す（どの問題が LLM 由来かを後で分析するため）。

---

## 8. 共同作業のルール

- **ipynb の同時編集は避ける。** ipynb は JSON なので、同じファイルを2人が編集すると衝突の解消が難しい。担当を決め、追加は新しいファイル（`_exNN` の次の番号）で行う。
- **`graph.yaml` は短い変更を早めにマージする。** 知識点の追加など、他の人の作業に影響する変更は先に PR を出す。
- **問題 ID は `assign-ids` に任せる。** 手で連番を付けると、別ブランチで同じ番号を使って衝突する。
- **一度取り込んだ ID（知識点・問題）は変えない。** 内容の修正は ID をそのままにして行う（取り込み時に版番号が上がる）。
- **問題を削除するときは PR に理由を書く。** 取り込み後は DB 上で「停止」になる（解答記録は残る）。
- **`docs/knowledge_graph_overview.md` は手で編集しない**（`graph-doc` で再生成する）。

---

## 9. よく出るエラーと直し方

`validate` の出力は `[ERROR] ファイル 問題 ID: メッセージ` の形式。

| メッセージ（抜粋） | 原因 | 直し方 |
| --- | --- | --- |
| `問題 ID がありません` | 見出しが `## 問題` のまま | `assign-ids` を実行する |
| `問題 ID が重複` | 別の問題と同じ ID | 片方の見出しを `## 問題` に戻して `assign-ids` |
| `存在しない知識点: …` | 知識点 ID の書き間違い、または `graph.yaml` に未追加 | ID を確認する（`docs/knowledge_graph_overview.md`） |
| `### 正解 には選択肢の記号だけを書いてください` | `**B**` や説明文を書いた | `B` または `A, C` だけにする |
| `正解 X が選択肢にありません` | 正解の記号が選択肢にない | 選択肢の数と正解を確認する |
| `選択肢の記号は A から順に` | `- A.` `- C.` のように記号が飛んでいる | `- A.` から順に書く |
| `選択肢（- A. ...）が2つ以上必要です` | 選択肢が認識されていない（`-A.` のように `-` の後に空白がない、`A)` と書いた など） | `- A. 選択肢` の形で書く |
| `旧形式の「### 答えと解説」です` | 古い書き方 | `### 正解` と `### 解説` に分ける |
| `模範解答がテスト N に失敗` | 模範解答かテストの期待値が間違っている | 模範解答を Jupyter で実行し、出力と `expected` を比べる |
| `初期コードのままで全テストに通ってしまいます` | テストが甘い／バグ取りのバグが再現しない | テストケースを追加する、`@starter` を見直す |
| `@starter のセルがありません` など | 1行目のマーカーがない、セルの種類が違う | code セルの1行目を `# @starter` にする。`@tests` は markdown セルの ` ```yaml ` の次の行 |
| `先修関係が循環しています: A → B → A` | 先修関係の向きの誤り | どちらが前提かを見直す |
| `関係が一つもない知識点`（警告） | 新しい知識点に関係を書いていない | 先修関係を1つ以上書く |
| `主知識点 X が単元 Y の範囲外です`（警告） | 単元の問題の先頭の知識点が範囲外 | 知識点の順番を入れ替えるか、単元の範囲を見直す |
| `講義ノートに正解・模範解答が含まれています` | 講義ノートに `### 正解` や `# @solution` を書いた | 練習ファイルに移す |
| `先頭にメタデータセル…がありません` | 1つ目のセルが ```` ```yaml ```` で始まっていない | テンプレートの1つ目のセルをコピーする |

それでも分からないときは、エラーの出力をそのまま PR やゼミのチャットに貼って相談する。

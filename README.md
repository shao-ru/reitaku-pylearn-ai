# reitaku-pylearn-ai

Python プログラミング教育のための知識グラフ・教材・AI 学習支援（麗澤大学 ゼミ開発リポジトリ）。

- **このリポジトリ（reitaku-pylearn-ai）**：知識グラフ、講義ノート・練習問題、教材ツール。今後、AI 学習支援サービス（出題・推薦、エラー診断、ヒント）もここで開発する。
- **練習プラットフォーム（reitaku-pylearn）**：学生がコードを書き、問題を解く Web システム（現在の暫定名 LearnLab）。このリポジトリの教材を取り込んで使う。

## はじめに

```powershell
git clone https://github.com/shao-ru/reitaku-pylearn-ai.git
cd reitaku-pylearn-ai
uv sync
uv run python -m tools.edu_content validate content/
```

`エラー 0 件` と出れば準備完了。教材を作る・追加する手順は [docs/authoring_guide.md](docs/authoring_guide.md) を参照。

## 構成

```
content/            教材コンテンツ（知識グラフ・講義ノート・練習問題・題単）
  units.yaml        トピックをまたぐ単元
  templates/        各ファイルのテンプレート
  var/ io/ cond/ col/ loop/ func/   文法層のトピック
  pat/              定型パターン（構造層）
  alg/ app/         アルゴリズム層・応用層（参考）
docs/
  knowledge_graph.md          知識グラフの設計方針（層・トピック・単元・関係）
  knowledge_graph_overview.md 知識グラフの一覧（自動生成）
  authoring_guide.md          教材の作成・追加ガイド
  content_format.md 教材コンテンツ形式の仕様書
  tools.md          教材ツールの実装
  migration/        移行時の ID 対応表
  schema/           JSON Schema
  todo.md           TODO
tools/
  edu_content/      教材の検証・ID 付与・JSON 出力・練習プラットフォーム用の教材出力ツール
```

## 教材ツール

```bash
uv sync                                   # 初回のみ：Python 3.12 と依存パッケージ（pyyaml）をインストール
uv run python -m tools.edu_content validate   content/
uv run python -m tools.edu_content assign-ids content/
uv run python -m tools.edu_content export     content/ -o build/json/
uv run python -m tools.edu_content courseware content/ -o build/courseware/
uv run python -m tools.edu_content graph-doc  content/ -o docs/knowledge_graph_overview.md
```

Python とパッケージの管理には [uv](https://docs.astral.sh/uv/) を使う（`pyproject.toml`・`uv.lock`）。

## ドキュメント

| 読む順 | 文書 | 内容 |
| --- | --- | --- |
| **学生** | [docs/student/README.md](docs/student/README.md) | **教材づくりを始める人はまずこれ**（手順・知識点一覧・見本） |
| 1 | [docs/knowledge_graph.md](docs/knowledge_graph.md) | 知識グラフの設計方針（層・トピック・知識点・単元・関係） |
| 2 | [docs/authoring_guide.md](docs/authoring_guide.md) | **教材を作る・追加する手順**、共同作業のルール、よく出るエラー |
| 3 | [docs/content_format.md](docs/content_format.md) | ファイル形式の仕様（属性・セクション・テスト・ID） |
| — | [docs/knowledge_graph_overview.md](docs/knowledge_graph_overview.md) | 現在の知識点・単元・関係の一覧（自動生成） |
| — | [docs/tools.md](docs/tools.md) | 教材ツールの実装・出力 JSON・拡張方法 |
| — | [docs/todo.md](docs/todo.md) | TODO |

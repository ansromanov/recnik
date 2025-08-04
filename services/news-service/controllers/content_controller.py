import os

from flask import jsonify
from openai import OpenAI

from models.news import ContentItem, ContentTemplate


class ContentController:
    """Controller for LLM-generated content (dialogues, summaries, etc.)"""

    def __init__(self, redis_client, db, logger):
        self.redis_client = redis_client
        self.db = db
        self.logger = logger
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        # Initialize OpenAI client
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None

        # Content type definitions
        self.content_types = {
            "dialogue": {
                "name": "Dialogue",
                "description": "Conversational dialogue between two or more people",
                "icon": "💬",
            },
            "summary": {
                "name": "Summary",
                "description": "Concise summary of news articles",
                "icon": "📝",
            },
            "story": {
                "name": "Story",
                "description": "Short story based on news topics",
                "icon": "📖",
            },
            "interview": {
                "name": "Interview",
                "description": "Simulated interview format",
                "icon": "🎤",
            },
            "vocabulary_exercise": {
                "name": "Vocabulary Exercise",
                "description": "Content focused on specific vocabulary words",
                "icon": "📚",
            },
        }

        # Initialize default templates
        self.initialize_templates()

    def initialize_templates(self):
        """Initialize default content templates if they don't exist"""
        try:
            # Check if templates already exist
            if ContentTemplate.query.first():
                return

            default_templates = [
                {
                    "name": "News Dialogue - Intermediate",
                    "content_type": "dialogue",
                    "description": "Two people discussing current news topic",
                    "difficulty_level": "intermediate",
                    "target_word_count": 200,
                    "prompt_template": """Create a dialogue in Serbian between two people discussing the topic: {topic}

Requirements:
- Use intermediate level Serbian vocabulary
- Include approximately {word_count} words
- Make it natural and conversational
- Focus on vocabulary that would be useful for Serbian learners
- Include some of these target words if provided: {target_words}
- Format as: Person A: [text] / Person B: [text]

Topic: {topic}
Difficulty: {difficulty}
Target words: {target_words}

Generate a natural dialogue:""",
                },
                {
                    "name": "News Summary - Brief",
                    "content_type": "summary",
                    "description": "Concise summary of news article",
                    "difficulty_level": "intermediate",
                    "target_word_count": 100,
                    "prompt_template": """Create a brief summary in Serbian of the following article.

Requirements:
- Use clear, intermediate-level Serbian
- Approximately {word_count} words
- Focus on main points and key information
- Make it easy to understand for Serbian learners

Article text: {article_text}

Write a clear summary:""",
                },
                {
                    "name": "Vocabulary Story",
                    "content_type": "story",
                    "description": "Short story incorporating target vocabulary",
                    "difficulty_level": "intermediate",
                    "target_word_count": 250,
                    "prompt_template": """Write a short story in Serbian that incorporates the topic: {topic}

Requirements:
- Use these target vocabulary words: {target_words}
- Approximately {word_count} words
- {difficulty} difficulty level
- Make it engaging and natural
- Help learners understand the vocabulary in context

Topic: {topic}
Target words: {target_words}
Difficulty: {difficulty}

Write the story:""",
                },
            ]

            for template_data in default_templates:
                template = ContentTemplate(**template_data)
                self.db.session.add(template)

            self.db.session.commit()
            self.logger.info(f"Initialized {len(default_templates)} default content templates")

        except Exception as e:
            self.logger.error(f"Error initializing templates: {e}")
            self.db.session.rollback()

    def generate_dialogue(self, topic, difficulty="intermediate", word_count=200):
        """Generate dialogue from topic using LLM"""
        try:
            if not self.openai_api_key:
                return jsonify({"error": "OpenAI API key not configured"}), 400

            # Get appropriate template
            template = ContentTemplate.query.filter_by(
                content_type="dialogue", difficulty_level=difficulty, is_active=True
            ).first()

            if not template:
                # Use default prompt if no template found
                prompt = f"""Create a dialogue in Serbian between two people discussing: {topic}

Make it natural, conversational, and approximately {word_count} words.
Use {difficulty} level vocabulary suitable for Serbian language learners.
Format as: Osoba A: [text] / Osoba B: [text]"""
            else:
                prompt = template.prompt_template.format(
                    topic=topic,
                    difficulty=difficulty,
                    word_count=word_count,
                    target_words="",
                )

            # Generate content using OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Serbian language teacher creating educational content for language learners.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )

            generated_content = response.choices[0].message.content.strip()

            # Calculate actual word count and reading time
            actual_word_count = len(generated_content.split())
            reading_time = max(1, round(actual_word_count / 200))

            # Save to database
            content_item = ContentItem(
                title=f"Dialogue: {topic}",
                content=generated_content,
                content_type="dialogue",
                topic=topic,
                difficulty_level=difficulty,
                generated_by=self.model,
                generation_prompt=prompt,
                word_count=actual_word_count,
                reading_time_minutes=reading_time,
            )

            self.db.session.add(content_item)
            self.db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "content": content_item.to_dict(),
                    "message": f"Generated dialogue about '{topic}'",
                }
            )

        except Exception as e:
            self.logger.error(f"Error generating dialogue: {e}")
            self.db.session.rollback()
            return jsonify({"error": "Failed to generate dialogue"}), 500

    def generate_summary(self, article_text, summary_type="brief"):
        """Generate summary from article using LLM"""
        try:
            if not self.openai_api_key:
                return jsonify({"error": "OpenAI API key not configured"}), 400

            # Determine word count based on summary type
            word_counts = {"brief": 100, "detailed": 200, "vocabulary_focused": 150}
            target_word_count = word_counts.get(summary_type, 100)

            # Create appropriate prompt based on summary type
            if summary_type == "vocabulary_focused":
                prompt = f"""Create a vocabulary-focused summary in Serbian of this article.

Requirements:
- Approximately {target_word_count} words
- Highlight important vocabulary words that would be useful for Serbian learners
- Use clear, intermediate-level language
- Focus on key terms and their context

Article: {article_text[:2000]}

Write a vocabulary-focused summary:"""
            else:
                prompt = f"""Create a {summary_type} summary in Serbian of this article.

Requirements:
- Approximately {target_word_count} words
- Use clear, intermediate-level Serbian
- Focus on main points and key information
- Make it accessible for Serbian language learners

Article: {article_text[:2000]}

Write the summary:"""

            # Generate summary
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating clear, educational summaries in Serbian for language learners.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=600,
            )

            generated_content = response.choices[0].message.content.strip()

            # Calculate metadata
            actual_word_count = len(generated_content.split())
            reading_time = max(1, round(actual_word_count / 200))

            # Extract topic from article (simple heuristic)
            topic = article_text.split(".")[0][:100] if "." in article_text else article_text[:100]

            # Save to database
            content_item = ContentItem(
                title=f"Summary: {topic}...",
                content=generated_content,
                content_type="summary",
                topic=topic,
                difficulty_level="intermediate",
                generated_by=self.model,
                generation_prompt=prompt,
                word_count=actual_word_count,
                reading_time_minutes=reading_time,
            )

            self.db.session.add(content_item)
            self.db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "content": content_item.to_dict(),
                    "message": f"Generated {summary_type} summary",
                }
            )

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            self.db.session.rollback()
            return jsonify({"error": "Failed to generate summary"}), 500

    def generate_vocabulary_context(self, topic, target_words=None, content_type="story"):
        """Generate vocabulary-focused content from topic"""
        try:
            if not self.openai_api_key:
                return jsonify({"error": "OpenAI API key not configured"}), 400

            if not target_words:
                target_words = []

            # Get appropriate template
            template = ContentTemplate.query.filter_by(
                content_type=content_type,
                difficulty_level="intermediate",
                is_active=True,
            ).first()

            target_words_str = (
                ", ".join(target_words) if target_words else "any relevant vocabulary"
            )

            if template:
                prompt = template.prompt_template.format(
                    topic=topic,
                    target_words=target_words_str,
                    difficulty="intermediate",
                    word_count=template.target_word_count,
                )
            else:
                # Default prompt
                prompt = f"""Create a {content_type} in Serbian about: {topic}

Requirements:
- Include these vocabulary words: {target_words_str}
- Use intermediate level Serbian
- Approximately 200 words
- Make it educational and engaging for Serbian learners
- Help learners understand vocabulary in context

Topic: {topic}
Vocabulary words to include: {target_words_str}

Create the {content_type}:"""

            # Generate content
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are creating educational Serbian content that helps language learners understand vocabulary in context.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )

            generated_content = response.choices[0].message.content.strip()

            # Calculate metadata
            actual_word_count = len(generated_content.split())
            reading_time = max(1, round(actual_word_count / 200))

            # Save to database
            content_item = ContentItem(
                title=f"{content_type.title()}: {topic}",
                content=generated_content,
                content_type=content_type,
                topic=topic,
                difficulty_level="intermediate",
                target_words=target_words,
                generated_by=self.model,
                generation_prompt=prompt,
                word_count=actual_word_count,
                reading_time_minutes=reading_time,
            )

            self.db.session.add(content_item)
            self.db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "content": content_item.to_dict(),
                    "message": f"Generated {content_type} with vocabulary focus",
                }
            )

        except Exception as e:
            self.logger.error(f"Error generating vocabulary context: {e}")
            self.db.session.rollback()
            return jsonify({"error": "Failed to generate vocabulary content"}), 500

    def get_content_types(self):
        """Get available content types"""
        return jsonify(
            {
                "content_types": self.content_types,
                "templates": [
                    t.to_dict() for t in ContentTemplate.query.filter_by(is_active=True).all()
                ],
            }
        )

    def get_recent_content(self, content_type="all", limit=10):
        """Get recently generated content"""
        try:
            query = ContentItem.query.order_by(ContentItem.created_at.desc())

            if content_type != "all":
                query = query.filter_by(content_type=content_type)

            content_items = query.limit(limit).all()

            return jsonify(
                {
                    "content": [item.to_dict() for item in content_items],
                    "total": len(content_items),
                    "content_type": content_type,
                }
            )

        except Exception as e:
            self.logger.error(f"Error getting recent content: {e}")
            return jsonify({"error": "Failed to get recent content"}), 500

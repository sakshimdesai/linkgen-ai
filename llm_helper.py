from groq_llm import generate_groq_post, generate_groq_hashtags

def llm(topic, length, language):
    post = generate_groq_post(topic, length, language)
    tags = generate_groq_hashtags(topic)

    return {
        "post": post,
        "hashtags": tags,
        "engagement": round(len(post) / 250, 2)
    }

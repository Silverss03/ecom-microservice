import tensorflow as tf
import numpy as np
import os
import json

# Load your CNN model
model_path = 'D:\\Code\\Python\\AI_for_ecom\\best_model_CNN_w2v.h5'  # Update with your actual path
model = tf.keras.models.load_model(model_path)

# Load your tokenizer
tokenizer_path = 'D:\\Code\\Python\\AI_for_ecom\\tokenizer.pickle'  # Update with your actual path
with open(tokenizer_path, 'r') as f:
    tokenizer_json = json.load(f)
    tokenizer = tf.keras.preprocessing.text.tokenizer_from_json(tokenizer_json)

# Maximum sequence length your model expects
max_sequence_length = 100  # Adjust to match your model's requirements

def preprocess_text(text):
    """Prepare text for sentiment analysis"""
    sequences = tokenizer.texts_to_sequences([text])
    padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(
        sequences, maxlen=max_sequence_length, padding='post'
    )
    return padded_sequences

def analyze_sentiment(text):
    """Process text with your CNN model and interpret results"""
    # Preprocess the text
    processed_text = preprocess_text(text)
    
    # Get prediction
    prediction = model.predict(processed_text)[0]
    
    # Convert prediction to sentiment score (-1 to 1 scale)
    sentiment_score = float(prediction[0])  # Assuming binary output
    normalized_score = (sentiment_score * 2) - 1
    
    # Determine sentiment category
    if normalized_score > 0.3:
        sentiment = "Positive"
    elif normalized_score < -0.3:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    
    return {
        "raw_score": sentiment_score,
        "normalized_score": normalized_score,
        "sentiment": sentiment
    }

# Test with examples of varying sentiment
test_samples = [
    # Positive examples
    "This product is amazing! The quality is outstanding and it works perfectly.",
    "I love the camera on this phone. The battery life is also excellent.",
    
    # Negative examples
    "Terrible purchase. It broke after a week and customer service was unhelpful.",
    "The quality is poor and it doesn't work as advertised. Very disappointed.",
    
    # Neutral examples
    "The product was okay. Nothing special but it works as described.",
    "It has some good features but also some drawbacks."
]

# Run tests
print("SENTIMENT ANALYSIS TEST RESULTS")
print("=" * 60)

for i, text in enumerate(test_samples):
    result = analyze_sentiment(text)
    
    print(f"TEST SAMPLE #{i+1}:")
    print(f"Text: {text}")
    print(f"Raw score: {result['raw_score']:.4f}")
    print(f"Normalized score: {result['normalized_score']:.4f} (-1 to 1 scale)")
    print(f"Interpreted sentiment: {result['sentiment']}")
    print("-" * 60)
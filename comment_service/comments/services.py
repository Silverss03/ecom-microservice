import numpy as np
import tensorflow as tf
import json
import os

class SentimentAnalysisService:
    def __init__(self):
        # Load your pre-trained CNN model
        model_path = os.path.join(os.path.dirname(__file__), '../models/cnn_sentiment_model')
        self.model = tf.keras.models.load_model(model_path)
        
        # Load your tokenizer or vocabulary
        with open(os.path.join(os.path.dirname(__file__), '../models/tokenizer.json'), 'r') as f:
            tokenizer_json = json.load(f)
            self.tokenizer = tf.keras.preprocessing.text.tokenizer_from_json(tokenizer_json)
            
        # Maximum sequence length your model expects
        self.max_sequence_length = 100
        
    def preprocess_text(self, text):
        """Convert text to the format expected by your CNN model"""
        # Tokenize and pad the text according to your model's requirements
        sequences = self.tokenizer.texts_to_sequences([text])
        padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(
            sequences, maxlen=self.max_sequence_length, padding='post'
        )
        return padded_sequences
        
    def analyze_text(self, text):
        """Analyze text using your CNN model and return sentiment data"""
        # Preprocess the text for the model
        processed_text = self.preprocess_text(text)
        
        # Get prediction from model
        prediction = self.model.predict(processed_text)[0]
        
        # Extract sentiment score (assuming binary sentiment: negative/positive)
        # For a multi-class model, adjust this accordingly
        sentiment_score = float(prediction[0])  # Convert to Python float
        
        # Extract aspects (keywords) from the text
        aspects = self.extract_key_aspects(text)
        
        return {
            'score': sentiment_score,  # Between 0-1, with 1 being most positive
            'normalized_score': (sentiment_score * 2) - 1,  # Convert to -1 to 1 scale
            'magnitude': abs((sentiment_score * 2) - 1),
            'aspects': aspects
        }
        
    def extract_key_aspects(self, text):
        """Extract key product aspects mentioned in the review text"""
        # Simple keyword extraction - replace with more sophisticated NLP if needed
        import spacy
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(text)
        
        aspects = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 1:
                aspects.append(chunk.text.lower())
                
        return aspects[:5]  # Return top 5 aspects
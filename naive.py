import pandas as pd
import numpy as np
import re
import yfinance as yf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Λειτουργία καθαρισμού κειμένου χωρίς NLTK
def preprocess_text(text):
    if pd.isna(text):
        return ""
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    words = text.split()  # Tokenize (χωρίς NLTK)
    words = [word for word in words if word not in ENGLISH_STOP_WORDS]  # Remove stopwords
    return " ".join(words)

# Φόρτωση δεδομένων εκπαίδευσης
train_df = pd.read_csv("twitter_tweets_sentiment.csv")

# Φόρτωση tweets προς ανάλυση
tweets_df = pd.read_csv("tweets.csv")

# Εκτύπωση στηλών για επιβεβαίωση
print("Columns in train_df:", train_df.columns.tolist())
print("Columns in tweets_df:", tweets_df.columns.tolist())

# Διόρθωση ονομάτων στηλών στο tweets_df
tweets_df.rename(columns={'Text': 'text', 'Created At': 'date'}, inplace=True)

# Καθαρισμός κειμένων
train_df['clean_text'] = train_df['text'].apply(preprocess_text)
tweets_df['clean_text'] = tweets_df['text'].apply(preprocess_text)

# Χρήση TfidfVectorizer για feature extraction
vectorizer = TfidfVectorizer()
X_train_tfidf = vectorizer.fit_transform(train_df['clean_text'])

# Στόχος ταξινόμησης (sentiment)
y_train = train_df['sentiment']

# Εκπαίδευση του Naïve Bayes μοντέλου
model = MultinomialNB()
model.fit(X_train_tfidf, y_train)

# Μετατροπή των tweets σε μορφή feature vector
tweets_tfidf = vectorizer.transform(tweets_df['clean_text'])

# Πρόβλεψη συναισθήματος για τα tweets
tweets_df['predicted_sentiment'] = model.predict(tweets_tfidf)

# **Μετατροπή των κατηγοριών του sentiment σε αριθμητικές τιμές**
sentiment_mapping = {'negative': -1, 'neutral': 0, 'positive': 1}
tweets_df['predicted_sentiment'] = tweets_df['predicted_sentiment'].map(sentiment_mapping)

# **Βεβαιώσου ότι η μετατροπή ήταν επιτυχής**
print("Unique values in predicted_sentiment after mapping:", tweets_df['predicted_sentiment'].unique())

# **Καθαρισμός ημερομηνιών των tweets**
tweets_df['date'] = pd.to_datetime(tweets_df['date'], errors='coerce').dt.date

# **Έλεγχος ημερομηνιών πριν το κατέβασμα δεδομένων**
start_date = tweets_df['date'].min()
end_date = tweets_df['date'].max()

# **Εκτύπωση ημερομηνιών για debugging**
print(f"Κατέβασμα BTC δεδομένων από {start_date} έως {end_date}")

# **Κατέβασμα ιστορικών τιμών του Bitcoin με ημερομηνίες**
if pd.notna(start_date) and pd.notna(end_date):
    btc_data = yf.download('BTC-USD', start=str(start_date), end=str(end_date))
    
    # **Έλεγχος αν τα δεδομένα κατεβάστηκαν σωστά**
    if btc_data.empty:
        print("⚠️ Δεν βρέθηκαν δεδομένα BTC για το επιλεγμένο χρονικό διάστημα!")
    else:
        # **Αποθήκευση των δεδομένων για έλεγχο**
        btc_data.to_csv("btc.csv")
        print("✅ Τα δεδομένα BTC αποθηκεύτηκαν επιτυχώς στο btc.csv")
else:
    print("❌ Σφάλμα: Οι ημερομηνίες έναρξης/λήξης είναι άκυρες!")

# **Καθαρισμός ημερομηνιών του BTC**
btc_data = btc_data[['Close']]
btc_data.reset_index(inplace=True)
btc_data.rename(columns={'Date': 'date', 'Close': 'btc_price'}, inplace=True)
btc_data['date'] = btc_data['date'].dt.date  # **Μετατροπή στο ίδιο format**

print(btc_data.columns)
print(tweets_df.columns)

if isinstance(btc_data.columns, pd.MultiIndex):
    btc_data.columns = btc_data.columns.get_level_values(0)

merged_df = pd.merge(tweets_df, btc_data, on='date', how='inner')




# **Βεβαίωση ότι το 'predicted_sentiment' έχει αριθμούς και όχι strings**
merged_df['predicted_sentiment'] = pd.to_numeric(merged_df['predicted_sentiment'], errors='coerce')

# Ομαδοποίηση ημερήσιου μέσου συναισθήματος
sentiment_agg = merged_df.groupby('date').agg({'predicted_sentiment': 'mean', 'btc_price': 'mean'})

# Οπτικοποίηση της σχέσης με δεύτερο άξονα Y
fig, ax1 = plt.subplots(figsize=(12,5))

ax1.set_xlabel('Date')
ax1.set_ylabel('Bitcoin Price', color='blue')
ax1.plot(sentiment_agg.index, sentiment_agg['btc_price'], label='Bitcoin Price', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

ax2 = ax1.twinx()  # Δημιουργία δεύτερου άξονα Y
ax2.set_ylabel('Avg Sentiment', color='red')
ax2.plot(sentiment_agg.index, sentiment_agg['predicted_sentiment'], label='Avg Sentiment', color='red')
ax2.tick_params(axis='y', labelcolor='red')

fig.suptitle('Sentiment of Tweets vs Bitcoin Price')
fig.autofmt_xdate(rotation=45)

plt.show()

# Αποθήκευση των αποτελεσμάτων
merged_df.to_csv("tweets_bitcoin_analysis.csv", index=False)

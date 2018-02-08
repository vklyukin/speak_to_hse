import nltk
import string
from nltk.corpus import stopwords

def tokenize_words(file_text):
    #firstly let's apply nltk tokenization
    tokens = nltk.word_tokenize(file_text)

    #delete punctuation symbols
    tokens = [i for i in tokens if ( i not in string.punctuation )]

    #deleting stop_words
    stop_words = stopwords.words('russian')
    stop_words.extend(['что', 'это', 'так', 'вот', 'быть', 'как', 'в', '—', 'к', 'на'])
    tokens = [i for i in tokens if ( i not in stop_words )]

    #cleaning words
    tokens = [i.replace("«", "").replace("»", "") for i in tokens]
    print(tokens)

    return tokens

import nltk
import pickle
from nltk.corpus import stopwords

#class of request for learning
class RequestItem:
    def __init__(self, request, type):
        self.request = request
        self.type = type

    def features(self, all_words):
        word_set = set(word for word in self.request)
        features = {}
        for w in all_words:
            features["w_%s" % w] = (w in word_set)
        return features

#creating of a list of all words in a training pool of requests
def collect_all_words(training_pool):
    all_words = []
    stop_words = stopwords.words('russian')
    for item in training_pool:
        for word in item.request:
            if word not in stop_words:
                all_words.append(word)
    return all_words

#creating of RequestItem objects
def create_pool_of_requests():
    pool = []
    file_name = 'testdata.txt'
    file = open(file_name, 'r')
    for line in file:
        request,type = line.split(';')
        request = request.split()
        pool.append(RequestItem(request,type))
    file.close()
    return pool

#classifier of requests
def classify_requests(pool, all_words):
    training_set = []
    for item in pool:
        features = item.features(all_words)
        tup = (features, item.type)  # tup is a 2-element tuple
        training_set.append(tup)
    classifier = nltk.NaiveBayesClassifier.train(training_set)
    return classifier

pool = create_pool_of_requests()
all_words = collect_all_words(pool)
classifier = classify_requests(pool,all_words)
filename = "naive_classify.sav"
pickle.dump(classifier, open(filename,'wb'))
print(classifier.classify(RequestItem(["покажи","расписание","майнеров"],"").features(all_words)))
print(classifier.classify(RequestItem(["привет","как", "дела"],"").features(all_words)))
print(classifier.classify(RequestItem(["покажи","расписание","завтра"],"").features(all_words)))
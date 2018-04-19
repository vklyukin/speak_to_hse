import nltk
import pickle
import random
import csv
import gensim
from nltk.corpus import stopwords
import pymorphy2
import numpy as np
import pandas as pd
import global_constants as gc

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
def train_requests(pool, all_words):
    feature_sets = []
    for item in pool:
        features = item.features(all_words)
        tup = (features, item.type)  # tup is a 2-element tuple
        feature_sets.append(tup)
    random.shuffle(feature_sets)
    size = int(len(feature_sets) * 0.2)
    training_set, test_set = feature_sets[size:], feature_sets[:size]

    classifier = nltk.DecisionTreeClassifier.train(training_set)
    print('Accuracy: {:4.2f}'.format(nltk.classify.accuracy(classifier, test_set)))
    return classifier

def vector_of_line(line: str, get_vector):
    morph = pymorphy2.MorphAnalyzer()
    words = line.split()
    vector = np.zeros_like(get_vector['расписание_NOUN'])
    for word in words:
        word = morph.normal_forms(word)[0]
        PoS = morph.parse(word)[0].tag.POS      #get part of speech
        try:
            vector += get_vector[word+'_'+PoS]
        except:
            """ """
    return vector

def create_dataset():
    decision_model_pkl = open(gc.submodel_filename, 'rb')
    decision_model = pickle.load(decision_model_pkl)
    get_vector = gensim.models.KeyedVectors.load_word2vec_format(r'''ruwikiruscorpora_upos_skipgram_300_2_2018.vec''')
    file_out = open(gc.requests_name, 'r')
    file_in = open(gc.dataset_name,'w', newline='')
    file_in_writer = csv.writer(file_in, delimiter=';')
    file_in_writer.writerow(["class_bayesian","minor","spam","common","help","response"])
    for line in file_out:
        words, response = line.split(';')
        vector = vector_of_line(words, get_vector)
        file_in_writer.writerow([str(classes[decision_model.classify(
            RequestItem(words.split(), '').features(all_words))]),str(get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "майнер_NOUN")),str(get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "спам_NOUN")),
        str(get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "расписание_NOUN")),str(get_vector.similarity(get_vector.most_similar(positive=[vector], topn=1)[0][0], "помощь_NOUN")),response])


classes = {"minor\n":-10, "spam\n":0, "common\n":10, "help\n":20}

pool = create_pool_of_requests()
all_words = collect_all_words(pool)
"""
classifier = train_requests(pool,all_words)
pickle.dump(classifier, open(gc.submodel_filename,'wb'))
#creating dataset
create_dataset()"""
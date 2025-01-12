# -*- coding: utf-8 -*-
"""
    @File   : textCateServer.py
    @Author : NLP_QiangShen (275171387@qq.com)
    @Time   : 2018/2/6 16:02
    @Todo   : 
"""

import json
import logging
import warnings

warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')

from bases.fileServer import FileServer
from nlp.basicTextProcessing import BasicTextProcessing
from nlp.naiveBayes4txtCate import MultinomialNB2TextCates
from nlp.textCate import TextCateServer
from gensim import corpora
from gensim import models

logger = logging.getLogger(__name__)


class TextCate(object):
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        """
        :param args:  args[0]={"txt": "textContent"}
        :param kwargs:
        :return: {"result": {"label": label, "prob": probability }}
        """
        rsp_json = False
        txt = json.loads(args[0]).get("txt", None)
        if txt:
            textHandler = BasicTextProcessing()
            logger.info("Splitting word for requesting text")
            wordSeqs = textHandler.doWordSplit(txt)[0]

            # 去停用词
            fileHandler = FileServer()
            logger.info("Loading stopWords")
            # stopWords = fileHandler.loadLocalGensimDict(path="/home/pamo/Codes/NLP_PAMO/Out/Dicts/",
            #                                             fileName="stopWords.dict")
            stopWords = fileHandler.loadLocalGensimDict(path="../../Out/Dicts/", fileName="stopWords.dict")
            if stopWords:
                logger.info("Loaded stopWords finished")
                wordSeqs = [word for word in wordSeqs if word not in stopWords.token2id.keys()]
                logger.info("Removed stopWords for requesting text finished")
            else:
                logger.warning("Loaded stopWords failed. Path of stopWords:%s")

            # 加载文本分类模型
            logger.info("Loading text classification model")
            # nbModel = fileHandler.loadPickledObjFile(path="/home/pamo/Codes/NLP_PAMO/Out/Models/",
            #                                          fileName="nbTextCate-2018.pickle")
            nbModel = fileHandler.loadPickledObjFile(path="../../Out/Models/", fileName="nbTextCate-2018.pickle")

            # 解析模型数据
            if nbModel:
                logger.info("Loaded text classification model finished")
                dicts = nbModel.dicts
                tfidf = nbModel.tfidf
                nbayes = nbModel.nbayes

                # 预处理测试文本
                logger.info("Preprocessing request text")
                txtsBow = []
                testVecs = []
                if isinstance(dicts, corpora.Dictionary):
                    txtsBow.append(dicts.doc2bow(wordSeqs))
                if isinstance(tfidf, models.TfidfModel):
                    testVecs = tfidf[txtsBow]
                # 生成测试文本的稀疏矩阵向量
                testVecs = list(testVecs)
                csrm_testVecs = TextCateServer.vecs2csrm(testVecs, len(dicts))
                logger.info("Preprocessing finished")
                # 文本类型预测
                if isinstance(nbayes, MultinomialNB2TextCates):
                    logger.info("Classifying text")
                    cateResult = nbayes.modelPredict(tdm=csrm_testVecs)[0]
                    if cateResult:
                        rsp_json = {"label": cateResult[0], "prob": "%.5f" % cateResult[1]}
            else:
                logger.error("Loaded text classification model failed")
        else:
            rsp_json = None

        if rsp_json:
            logger.info("Classifying text successed")
        else:
            logger.error("Classifying text failed")
        return rsp_json


app = TextCate()


def main():
    # 测试数据预处理
    txt = "1月4日，东四路居民张某，在微信聊天上认识一位自称为香港做慈善行业的好友，对方称自己正在做慈善抽奖活动，因与张某关系好，" \
          "特给其预留了30万中奖名额，先后以交个人所得税、押金为名要求张某以无卡存款的形式向其指定的账户上汇款60100元"
    cateResult = app(json.dumps({"txt": txt}))
    print(cateResult)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s | %(levelname)s | %(filename)s(line:%(lineno)s) | %(message)s",
                        datefmt="%Y-%m-%d(%A) %H:%M:%S")
    main()

# coding: UTF-8

from .base import BasePipeline


class DefaultPipeline(BasePipeline):
    """
    프로토타입으로 멀티 스레드도 아니며, 메시지간의 순서도 지키지 않으며 동작하는 파이프라인.
    추후 이 클래스를 지우고, 각각의 특징이 있는 다른 파이프라인을 개발이 필요함.
    """
    pass

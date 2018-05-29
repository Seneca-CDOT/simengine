from neo4j.v1 import GraphDatabase, basic_auth

driver = GraphDatabase.driver('bolt://localhost',auth=basic_auth("test", "test"))

def get_db():
    return driver.session()
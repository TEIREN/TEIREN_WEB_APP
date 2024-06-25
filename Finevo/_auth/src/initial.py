from common.neo4j.handler import Neo4jHandler

class InitDatabase(Neo4jHandler):
    def __init__(self, user_db) -> None:
        super().__init__()
        self.user_db = user_db
    
    def compliance(self) -> bool:
        cypher = """
        LOAD CSV FROM 'file:///isms-p.csv' AS row
        WITH row[0] AS row0, row[1] AS row1, row[2] AS row2, row[3] AS row3, row[4] AS row4, row[5] AS row5, row[6] AS row6, row[7] AS row7, row[8] AS row8
        
        MERGE (n:Compliance{name:'Compliance'})
        MERGE (l:Compliance:Certification {name: 'Isms_p', renew:36, applicable_country:'Korea'})
        MERGE (v:Version:Compliance {name: 'Isms_p', date:date('2023-10-31')})
        MERGE (n)-[:COMPLIANCE]->(l)
        MERGE (l)-[:VERSION]->(v)
        
        WITH row0, row1, row2, row3, row4, row5, row6, row7, row8, n, l, v
        
        CALL apoc.do.case([
            row0 IS NULL AND row2 IS NULL AND row4 IS NOT NULL,
            'MERGE (a:Article:Compliance:Certification {compliance_name: "Isms_p", no: row4, name: row5, comment: row6})
            MERGE (v)-[:ARTICLE]->(a)
            RETURN a',
            row0 IS NOT NULL AND row2 IS NULL AND row4 IS NOT NULL,
            'MERGE (c:Chapter:Compliance:Certification{compliance_name:"Isms_p", no:row0, name:row1})
            MERGE (a:Article:Compliance:Certification {compliance_name: "Isms_p", no: row4, name: row5, comment: row6})
            MERGE (v)-[:CHAPTER]->(c)
            MERGE (c)-[:ARTICLE]->(a)
            RETURN a',
            row0 IS NOT NULL AND row2 IS NOT NULL AND row4 IS NOT NULL,
            'MERGE (c:Chapter:Compliance:Certification{compliance_name:"Isms_p", no:row0, name:row1})
            MERGE (s:Section:Compliance:Certification {compliance_name: "Isms_p", no: row2, name: row3})
            MERGE (a:Article:Compliance:Certification {compliance_name: "Isms_p", no: row4, name: row5, comment: row6})
            MERGE (v)-[:CHAPTER]->(c)
            MERGE (c)-[:SECTION]->(s)
            MERGE (s)-[:ARTICLE]->(a)
            RETURN a'
        ],
            'RETURN row2',
            {
                row0:row0,
                row1:row1,
                row2:row2,
                row3:row3,
                row4:row4,
                row5:row5,
                row6:row6,
                v:v
            }
        )
        YIELD value
        
        WITH row4, row6, row7, row8, value.a AS a, n, l, v
        WHERE row4 CONTAINS a.no
        WITH collect(row7) AS collect, split(replace(row8, "\n", ""), '_')[1..] AS example, a, n, l, v
        SET a.checklist = collect, a.example = example
        RETURN n, l, v
        """
        try:
            self.run(database=self.user_db, query=cypher)
            return True
        except Exception as e:
            print(f'Error: Can not overwrite compliance -> {e}')
            return False
        
    def gdpr(self) -> bool:
        cypher = """
        LOAD CSV FROM 'file:///gdpr.csv' AS row
        WITH row[0] AS row0, row[1] AS row1, row[2] AS row2, row[3] AS row3, row[4] AS row4, row[5] AS row5, row[6] AS row6

        MERGE (n:Compliance{name:'Compliance'})
        MERGE (l:Compliance:Law {name: 'Gdpr'})
        MERGE (v:Version:Compliance {name: 'Gdpr', date:date('2018-05-25')})
        MERGE (n)-[:COMPLIANCE]->(l)
        MERGE (l)-[:VERSION]->(v)

        WITH row0, row1, row2, row3, row4, row5, row6, n, l, v

        CALL apoc.do.case([
            row0 IS NULL AND row2 IS NULL AND row4 IS NOT NULL,
            'MERGE (a:Article:Compliance:Certification {compliance_name: "Gdpr", no: row4, name: row5, comment: row6})
            MERGE (v)-[:ARTICLE]->(a)
            RETURN a',
            row0 IS NOT NULL AND row2 IS NULL AND row4 IS NOT NULL,
            'MERGE (c:Law:Chapter:Compliance {compliance_name:"Gdpr",no:row0, name:row1})
            MERGE (a:Article:Compliance:Law {compliance_name: "Gdpr", no: row4, name: row5})
            MERGE (v)-[:CHAPTER]->(c)
            MERGE (c)-[:ARTICLE]->(a)
            RETURN a',
            row0 IS NOT NULL AND row2 IS NOT NULL AND row4 IS NOT NULL,
            'MERGE (c:Law:Chapter:Compliance {compliance_name:"Gdpr",no:row0, name:row1})
            MERGE (s:Section:Compliance:Law {compliance_name: "Gdpr", no: row2, name: row3})
            MERGE (a:Article:Compliance:Law {compliance_name: "Gdpr", no: row4, name: row5})
            MERGE (v)-[:CHAPTER]->(c)
            MERGE (c)-[:SECTION]->(s)
            MERGE (s)-[:ARTICLE]->(a)
            RETURN a'
        ],
            'RETURN row2',
            {row0:row0, row1:row1, row2:row2, row3:row3, row4:row4, row5:row5, row6:row6, v:v}
        )
        YIELD value

        WITH row4, row6, value.a AS a, n, l, v
        WHERE row4 CONTAINS a.no
        WITH collect(row6) AS collect, a, n, l, v
        SET a.comment = collect
        RETURN n, l, v
        """
        try:
            self.run(database=self.user_db, query=cypher)
            return True
        except Exception as e:
            print(f'Error: Can not overwrite compliance -> {e}')
            return False
    
    def isms_p_mapping(self) -> bool:
        cypher = """
        LOAD CSV FROM 'file:///ismsp_mapping.csv' AS row
        WITH row[0] AS row0, row[1] AS row1, row[2] AS row2, row[3] AS row3, row[4] AS row4

        MATCH (i:Compliance:Certification:Article{compliance_name:'Isms_p'})
        MATCH (l:Compliance:Law:Article)
        WHERE i.no = row0
            AND l.compliance_name = row2
            AND l.no = row3
        MERGE (i)<-[:MAPPED]->(l)

        return i, l
        """
        try:
            self.run(database=self.user_db, query=cypher)
            return True
        except Exception as e:
            print(f'Error: Can not overwrite compliance -> {e}')
            return False
    
    def product(self) -> bool:
        cypher = """
        MERGE (n:Compliance{name:'Compliance'})
        MERGE (e:Compliance:Evidence {name: 'Evidence'})
        MERGE (n)-[:COMPLIANCE]->(e)
        MERGE (p:Compliance:Evidence:Product {name:'Policy Manage'})
        MERGE (p1:Compliance:Evidence:Policy {name: 'Articles of Association'})
        MERGE (p2:Compliance:Evidence:Policy {name: 'Rules'})
        MERGE (p3:Compliance:Evidence:Policy {name: 'Guidelines'})
        MERGE (p4:Compliance:Evidence:Policy {name: 'Regulation'})
        MERGE (e)-[:PRODUCT]->(p)
        MERGE (p)-[:POLICY]->(p1)
        MERGE (p)-[:POLICY]->(p2)
        MERGE (p)-[:POLICY]->(p3)
        MERGE (p)-[:POLICY]->(p4) 
        MERGE (a:Compliance:Evidence:Product {name:'Asset Manage'})
        MERGE (f:Compliance:Evidence:Data {name: 'File'})
        MERGE (e)-[:PRODUCT]->(a)
        MERGE (a)-[:DATA]->(f)
        
        RETURN 1
        """
        try:
            self.run(database=self.user_db, query=cypher)
            return True
        except Exception as e:
            print(f'Error: Can not overwrite compliance -> {e}')
            return False
    
    def product_2(self) -> bool:
        cypher = """
        MATCH (n:Compliance{name:'Compliance'})
        MERGE (e:Compliance:Evidence {name: 'Evidence'})
        MERGE (n)-[:COMPLIANCE]->(e)
        MERGE (p:Compliance:Evidence:Product {name:'AWS'})
        MERGE (e)-[:PRODUCT]->(p)
        """
        try:
            self.run(database=self.user_db, query=cypher)
            return True
        except Exception as e:
            print(f'Error: Can not overwrite compliance -> {e}')
            return False
        
    def super_node(self) -> bool:
        init_node_list = ['Iam', 'Root', 'Role', 'Etc', 'Ec2', 'Lambda', 'AwsAccount', 'Unknown']
        for init_node in init_node_list:
            cypher = f"""
            CREATE (node:Super:{init_node})
            SET node.name = '{init_node}'
            RETURN 1
            """
            try:
                self.run(database=self.user_db, query=cypher)
            except Exception as e:
                print(f'Error: Can not overwrite compliance -> {e}')
                return False
        return True

    def sub_node(self) -> bool:
        cloudwatch_node_list = [['Elb', 'Sub']]
        for label_list in cloudwatch_node_list:
            cypher = f"""
            CREATE (node:{':'.join(label_list)})
            RETURN node
            """
            try:
                self.run(database=self.user_db, query=cypher)
            except Exception as e:
                print(f'Error: Can not overwrite compliance -> {e}')
                return False
        return True
    
    def detect_node(self) -> bool:
        from .query.rule_detect_query import rule_detect_query
        from .query.flow_rule_detect_query import flow_rule_detect_query
        from .query.test_detect_query import test_rule_detect_query
        from .query.init_merge_detect_node import init_merge_detect_query

        for cypher in rule_detect_query:
            try:
                self.run(database=self.user_db, query=cypher)
            except Exception as e:
                print(e)
                return False
        for cypher in flow_rule_detect_query:
            try:
                self.run(database=self.user_db, query=cypher)
            except Exception as e:
                print(e)
                return False
        for cypher in test_rule_detect_query:
            try:
                self.run(database=self.user_db, query=cypher)
            except Exception as e:
                print(e)
                return False
        for cypher in init_merge_detect_query:
            try:
                self.run(database=self.user_db, query=cypher)
            except Exception as e:
                print(e)
                return False
        return True
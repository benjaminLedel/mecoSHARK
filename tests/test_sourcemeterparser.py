import csv
import os
import shutil
import unittest

from bson import ObjectId
from mongoengine.connection import get_connection
from pathlib import Path

from mongoengine import connect
from pymongo import MongoClient

from mecoshark.resultparser.sourcemeterparser import SourcemeterParser
from pycoshark.mongomodels import VCSSystem, Commit, Project, File


class SourceMeterParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize mongoclient
        cls.mongoClient = MongoClient("mongodb", 27017)

        # Setting up database with data that is normally put into it via vcs program
        c1 = connect('meco_run', username=None, password=None, host='mongodb', port=27017, authentication_source=None,
                connect=False)
        print(c1)

    def setUp(self):
        # Setup logging
        self.input_path_python = os.path.dirname(os.path.realpath(__file__)) + '/data/python_project'
        self.input_path_java = os.path.dirname(os.path.realpath(__file__)) + '/data/java_project2'
        self.out_java = os.path.dirname(os.path.realpath(__file__)) + '/data/out_java'



        # Clear database first (we need a small hack here, as mongomocks drop_database does not work)
        self.mongoClient.drop_database("meco_run")
        #Project.drop_collection()
        #VCSSystem.drop_collection()
        #File.drop_collection()
        #Commit.drop_collection()

        self.project_id = Project(name="zookeeper").save().id
        self.vcs_id = VCSSystem(url="http://test.de", project_id=self.project_id, repository_type="test").save().id
        self.commit_id = Commit(revision_hash="2342", vcs_system_id=self.vcs_id).save()
        self.file1 = File(path="contribs/CekiGulcu/AppenderTable.java", vcs_system_id=self.vcs_id).save()
        self.file2 = File(path="contribs/LeosLiterak/TempFileAppender.java", vcs_system_id=self.vcs_id).save()
        self.file3 = File(path="src/main/java/org/apache/log4j/AsyncAppender.java", vcs_system_id=self.vcs_id).save()

        shutil.rmtree(self.out_java, ignore_errors=True)
        shutil.rmtree(self.input_path_java, ignore_errors=True)
        os.makedirs(self.out_java)

        # Copying up fake files that are generated by SourceMeter
        self.class_csv = os.path.dirname(os.path.realpath(__file__)) + '/data/csv_data/zookeeper-Class.csv'
        self.package_csv = os.path.dirname(os.path.realpath(__file__)) + '/data/csv_data/zookeeper-Package.csv'
        self.component_csv = os.path.dirname(os.path.realpath(__file__)) + '/data/csv_data/zookeeper-Component.csv'
        shutil.copy(self.class_csv, self.out_java)
        shutil.copy(self.package_csv, self.out_java)
        shutil.copy(self.component_csv, self.out_java)

        # Create Files and directories
        os.makedirs(self.input_path_java + '/contribs/CekiGulcu')
        os.makedirs(self.input_path_java + '/contribs/LeosLiterak')
        os.makedirs(self.input_path_java + '/src/main/java/org/apache/log4j')

        Path(self.input_path_java + '/contribs/CekiGulcu/AppenderTable.java').touch()
        Path(self.input_path_java + '/contribs/LeosLiterak/TempFileAppender.java').touch()
        Path(self.input_path_java + '/src/main/java/org/apache/log4j/AsyncAppender.java').touch()

    def test_initialization(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        self.assertEqual(self.commit_id.id, parser.commit_id)
        self.assertIsInstance(parser.commit_id, ObjectId)

        self.assertEqual(self.vcs_id, parser.vcs_system_id)
        self.assertIsInstance(parser.vcs_system_id, ObjectId)


    '''
    def test_initialization_fails_commit_id_wrong(self):
        # It should make a sys.exit call, as our vcs program was not executed
        with self.assertRaises(SystemExit) as cm:
            parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "42", 'DEBUG')

        self.assertEqual(cm.exception.code, 1)

    def test_initialization_fails_vcs_system_url_wrong(self):
        # It should make a sys.exit call, as our vcs program was not executed
        with self.assertRaises(SystemExit) as cm:
            parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "42", 'DEBUG')

        self.assertEqual(cm.exception.code, 1)

    def test_find_stored_files(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        expected_output = {
            'contribs/CekiGulcu/AppenderTable.java': self.file1.id,
            'contribs/LeosLiterak/TempFileAppender.java': self.file2.id,
            'src/main/java/org/apache/log4j/AsyncAppender.java': self.file3.id,
        }

        self.assertDictEqual(expected_output, parser.find_stored_files())

    def test_get_csv_file(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        class_file = os.path.join(self.out_java, "*-Class.csv")
        package_file = os.path.join(self.out_java, "*-Package.csv")
        component_file = os.path.join(self.out_java, "*-Component.csv")

        self.assertEqual(self.out_java+'/zookeeper-Class.csv', parser.get_csv_file(class_file))
        self.assertEqual(self.out_java+'/zookeeper-Package.csv', parser.get_csv_file(package_file))
        self.assertEqual(self.out_java+'/zookeeper-Component.csv', parser.get_csv_file(component_file))

    def test_get_csv_file_fails(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        class_file = os.path.join(self.out_java, "*-NotExisting.csv")

        self.assertEqual(None, parser.get_csv_file(class_file))

    def test_sort_for_parent(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')

        file1_metrics = {
            'sortKey': '2',
            'LongName': '<root_package>',
            'type': 'package',
            'ID': '103',
            'Parent': '__LogicalRoot__'
        }

        file2_metrics = {
            'sortKey': '103',
            'LongName': 'org',
            'type': 'package',
            'ID': '104',
            'Parent': '103'
        }

        file3_metrics = {
            'sortKey': '104',
            'LongName': 'org/Class1.java',
            'type': 'class',
            'ID': '105',
            'Parent': '104'
        }

        file4_metrics = {
            'sortKey': '107',
            'LongName': 'org/package1/Class2.java',
            'type': 'class',
            'ID': '106',
            'Parent': '107'
        }

        file5_metrics = {
            'sortKey': '104',
            'LongName': 'package1',
            'type': 'package',
            'ID': '107',
            'Parent': '104'
        }

        all_files = [file1_metrics, file2_metrics, file3_metrics, file5_metrics, file4_metrics]

        # Must not timeout
        parser.sort_for_parent(all_files)

    def test_sanitize_long_name_file(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        self.assertEqual('contribs/CekiGulcu/AppenderTable.java',
                         parser.sanitize_long_name(self.input_path_java + '/contribs/CekiGulcu/AppenderTable.java'))

    def test_sanitize_long_name_meta_package1(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        self.assertEqual('org.apache', parser.sanitize_long_name('org.apache'))

    def test_sanitize_long_name_meta_package2(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        self.assertEqual('unnamed package', parser.sanitize_long_name('unnamed package'))

    def test_sanitize_long_name_meta_package3(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        self.assertEqual('<System>', parser.sanitize_long_name('<System>'))

    def test_sanitize_long_name_class(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        self.assertEqual('org.apache.log4j.TempFileAppender',
                         parser.sanitize_long_name('org.apache.log4j.TempFileAppender'))

    def test_sanitize_metrics_dictionary_components(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        expected_output_component_1 = {'TNA': 1517.0, 'TNFI': 363.0, 'TLOC': 70281.0, 'CEG': 0.0, 'TNDI': 99.0,
                                       'TNPEN': 0.0, 'CLC': 0.0587641, 'TNIN': 27.0, 'TAD': 0.73795, 'CCO': 718.0,
                                       'CCL': 144.0, 'TNPKG': 52.0, 'TCLOC': 25645.0, 'TNM': 3553.0, 'CC': 0.108906,
                                       'CLLC': 0.102312, 'LDC': 4130.0, 'NCR': 0.107773, 'LLDC': 3580.0, 'CEE': 0.0,
                                       'TNOS': 16895.0, 'TNPA': 210.0, 'TNCL': 516.0, 'TPUA': 772.0, 'TNG': 505.0,
                                       'TNPM': 2910.0, 'TNS': 327.0, 'TLLOC': 35217.0, 'CR': 0.0, 'TPDA': 2174.0,
                                       'CI': 404.0, 'TNEN': 0.0, 'TNPCL': 339.0, 'TNPIN': 24.0, 'TCD': 0.421363}

        expected_output_component_2 = {'TNA': 1517.0, 'TNFI': 363.0, 'TLOC': 70281.0, 'CEG': 0.0, 'TNDI': 99.0,
                                       'TNPEN': 0.0, 'CLC': 0.0587641, 'TNIN': 27.0, 'TAD': 0.73795, 'CCO': 718.0,
                                       'CCL': 144.0, 'TNPKG': 52.0, 'TCLOC': 25645.0, 'TNM': 3553.0, 'CC': 0.108906,
                                       'CLLC': 0.102312, 'LDC': 4130.0, 'NCR': 0.107773, 'LLDC': 3580.0, 'CEE': 0.0,
                                       'TNOS': 16895.0, 'TNPA': 210.0, 'TNCL': 516.0, 'TPUA': 772.0, 'TNG': 505.0,
                                       'TNPM': 2910.0, 'TNS': 327.0, 'TLLOC': 35217.0, 'CR': 0.0, 'TPDA': 2174.0,
                                       'CI': 404.0, 'TNEN': 0.0, 'TNPCL': 339.0, 'TNPIN': 24.0, 'TCD': 0.421363}

        output = []
        with open(self.component_csv) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                output.append(parser.sanitize_metrics_dictionary(row))

        self.assertEqual(output[0], expected_output_component_1)
        self.assertEqual(output[1], expected_output_component_2)

    def test_sanitize_metrics_dictionary_classes(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        expected_output_class_1 = {'CI': 1.0, 'TNLPM': 5.0, 'CCL': 1.0, 'CLOC': 28.0, 'TNLS': 0.0, 'NOD': 0.0,
                                   'NOS': 30.0, 'NL': 1.0, 'WMC': 5.0, 'LCOM5': 1.0, 'CLC': 0.0973451, 'TNM': 5.0,
                                   'TNLM': 5.0, 'TNPM': 5.0, 'TNLA': 2.0, 'DLOC': 26.0, 'PUA': 2.0, 'TLLOC': 72.0,
                                   'LOC': 86.0, 'CBO': 6.0, 'AD': 0.5, 'NPM': 3.0, 'CD': 0.358974, 'NOC': 0.0,
                                   'NPA': 0.0, 'NLPM': 3.0, 'TNPA': 0.0, 'CLLC': 0.0972222, 'CCO': 1.0, 'NLA': 1.0,
                                   'PDA': 2.0, 'NS': 0.0, 'TNLPA': 0.0, 'NM': 3.0, 'NLG': 0.0, 'NG': 0.0, 'TNG': 1.0,
                                   'RFC': 9.0, 'TNLG': 1.0, 'NLE': 1.0, 'NLM': 3.0, 'CC': 0.169492, 'CBOI': 1.0,
                                   'NLS': 0.0, 'TNA': 2.0, 'LLOC': 50.0, 'TLOC': 113.0, 'NLPA': 0.0, 'LDC': 11.0,
                                   'NA': 1.0, 'NOI': 6.0, 'TNOS': 37.0, 'TCD': 0.327103, 'NOA': 0.0, 'NII': 1.0,
                                   'LLDC': 7.0, 'TNS': 0.0, 'DIT': 0.0, 'TCLOC': 35.0, 'NOP': 0.0}

        expected_output_class_2 = {'CI': 0.0, 'TNLPM': 6.0, 'CCL': 0.0, 'CLOC': 83.0, 'TNLS': 1.0, 'NOD': 0.0,
                                   'NOS': 29.0, 'NL': 4.0, 'WMC': 21.0, 'LCOM5': 3.0, 'CLC': 0.0, 'TNM': 26.0,
                                   'TNLM': 8.0, 'TNPM': 22.0, 'TNLA': 7.0, 'DLOC': 67.0, 'PUA': 2.0, 'TLLOC': 68.0,
                                   'LOC': 151.0, 'CBO': 4.0, 'AD': 0.714286, 'NPM': 22.0, 'CD': 0.549669, 'NOC': 0.0,
                                   'NPA': 3.0, 'NLPM': 6.0, 'TNPA': 3.0, 'CLLC': 0.0, 'CCO': 0.0, 'NLA': 7.0,
                                   'PDA': 5.0, 'NS': 5.0, 'TNLPA': 3.0, 'NM': 26.0, 'NLG': 1.0, 'NG': 7.0, 'TNG': 7.0,
                                   'RFC': 11.0, 'TNLG': 1.0, 'NLE': 2.0, 'NLM': 8.0, 'CC': 0.0, 'CBOI': 0.0, 'NLS': 1.0,
                                   'TNA': 14.0, 'LLOC': 68.0, 'TLOC': 151.0, 'NLPA': 3.0, 'LDC': 0.0, 'NA': 14.0,
                                   'NOI': 3.0, 'TNOS': 29.0, 'TCD': 0.549669, 'NOA': 3.0, 'NII': 0.0, 'LLDC': 0.0,
                                   'TNS': 5.0, 'DIT': 2.0, 'TCLOC': 83.0, 'NOP': 1.0}

        expected_output_class_3 = {'CI': 1.0, 'TNLPM': 22.0, 'CCL': 1.0, 'CLOC': 184.0, 'TNLS': 3.0, 'NOD': 0.0,
                                   'NOS': 80.0, 'NL': 3.0, 'WMC': 36.0, 'LCOM5': 2.0, 'CLC': 0.0240296, 'TNM': 40.0,
                                   'TNLM': 22.0, 'TNPM': 38.0, 'TNLA': 15.0, 'DLOC': 137.0, 'PUA': 0.0, 'TLLOC': 240.0,
                                   'LOC': 376.0, 'CBO': 8.0, 'AD': 1.0, 'NPM': 33.0, 'CD': 0.533333, 'NOC': 0.0,
                                   'NPA': 1.0, 'NLPM': 17.0, 'TNPA': 1.0, 'CLLC': 0.0458333, 'CCO': 4.0, 'NLA': 9.0,
                                   'PDA': 18.0, 'NS': 7.0, 'TNLPA': 1.0, 'NM': 35.0, 'NLG': 5.0, 'NG': 11.0,
                                   'TNG': 11.0, 'RFC': 38.0, 'TNLG': 5.0, 'NLE': 3.0, 'NLM': 17.0, 'CC': 0.0523752,
                                   'CBOI': 5.0, 'NLS': 3.0, 'TNA': 22.0, 'LLOC': 161.0, 'TLOC': 541.0, 'NLPA': 1.0,
                                   'LDC': 13.0, 'NA': 16.0, 'NOI': 21.0, 'TNOS': 119.0, 'TCD': 0.515152, 'NOA': 4.0,
                                   'NII': 10.0, 'LLDC': 11.0, 'TNS': 7.0, 'DIT': 2.0, 'TCLOC': 255.0, 'NOP': 2.0}


        output = []
        with open(self.class_csv) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                output.append(parser.sanitize_metrics_dictionary(row))

        self.assertEqual(output[0], expected_output_class_1)
        self.assertEqual(output[1], expected_output_class_2)
        self.assertEqual(output[2], expected_output_class_3)

    def test_sanitize_metrics_dictionary_packages(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        expected_output_package_1 = {'NIN': 0.0, 'TAD': 0.73795, 'CLC': 0.0587641, 'TNS': 327.0, 'TNM': 3553.0,
                                     'TNPM': 2910.0, 'TNG': 505.0, 'NCL': 0.0, 'TLOC': 70281.0, 'TNCL': 516.0,
                                     'TNDI': 99.0, 'TLLOC': 35217.0, 'PDA': 0.0, 'NPM': 0.0, 'TNPEN': 0.0, 'NG': 0.0,
                                     'TNPA': 210.0, 'NS': 0.0, 'LLOC': 0.0, 'NM': 0.0, 'CLOC': 0.0, 'LOC': 0.0,
                                     'TCD': 0.421363, 'CCL': 144.0, 'TNOS': 16895.0, 'TNPKG': 52.0, 'PUA': 0.0,
                                     'CI': 404.0, 'CC': 0.108906, 'LDC': 4130.0, 'AD': 0.0, 'TNIN': 27.0, 'TNEN': 0.0,
                                     'NA': 0.0, 'NPKG': 4.0, 'TNPCL': 339.0, 'NPA': 0.0, 'TCLOC': 25645.0, 'NEN': 0.0,
                                     'CD': 0.0, 'TNA': 1517.0, 'TNPIN': 24.0, 'CLLC': 0.102312, 'CCO': 718.0,
                                     'TPDA': 2174.0, 'TNFI': 363.0, 'TPUA': 772.0, 'LLDC': 3580.0}

        expected_output_package_2 = {'NIN': 0.0, 'TAD': 0.76, 'CLC': 0.0447154, 'TNS': 4.0, 'TNM': 42.0, 'TNPM': 37.0,
                                     'TNG': 15.0, 'NCL': 13.0, 'TLOC': 1154.0, 'TNCL': 13.0, 'TNDI': 13.0,
                                     'TLLOC': 466.0, 'PDA': 19.0, 'NPM': 37.0, 'TNPEN': 0.0, 'NG': 15.0, 'TNPA': 1.0,
                                     'NS': 4.0, 'LLOC': 466.0, 'NM': 42.0, 'CLOC': 512.0, 'LOC': 1154.0,
                                     'TCD': 0.523517, 'CCL': 4.0, 'TNOS': 194.0, 'TNPKG': 0.0, 'PUA': 6.0, 'CI': 6.0,
                                     'CC': 0.179418, 'LDC': 11.0, 'AD': 0.76, 'TNIN': 0.0, 'TNEN': 0.0, 'NA': 35.0,
                                     'NPKG': 0.0, 'TNPCL': 6.0, 'NPA': 1.0, 'TCLOC': 512.0, 'NEN': 0.0, 'CD': 0.523517,
                                     'TNA': 35.0, 'TNPIN': 0.0, 'CLLC': 0.0542636, 'CCO': 16.0, 'TPDA': 19.0,
                                     'TNFI': 6.0, 'TPUA': 6.0, 'LLDC': 7.0}

        expected_output_package_3 = {'NIN': 0.0, 'TAD': 0.733906, 'CLC': 0.0573787, 'TNS': 311.0, 'TNM': 3391.0,
                                     'TNPM': 2772.0, 'TNG': 474.0, 'NCL': 0.0, 'TLOC': 64937.0, 'TNCL': 468.0,
                                     'TNDI': 83.0, 'TLLOC': 32802.0, 'PDA': 0.0, 'NPM': 0.0, 'TNPEN': 0.0, 'NG': 0.0,
                                     'TNPA': 185.0, 'NS': 0.0, 'LLOC': 0.0, 'NM': 0.0, 'CLOC': 0.0, 'LOC': 0.0,
                                     'TCD': 0.417454, 'CCL': 136.0, 'TNOS': 15663.0, 'TNPKG': 30.0, 'PUA': 0.0,
                                     'CI': 377.0, 'CC': 0.104568, 'LDC': 3726.0, 'AD': 0.0, 'TNIN': 23.0, 'TNEN': 0.0,
                                     'NA': 0.0, 'NPKG': 1.0, 'TNPCL': 305.0, 'NPA': 0.0, 'TCLOC': 23506.0, 'NEN': 0.0,
                                     'CD': 0.0, 'TNA': 1370.0, 'TNPIN': 20.0, 'CLLC': 0.0994694, 'CCO': 660.0,
                                     'TPDA': 2052.0, 'TNFI': 326.0, 'TPUA': 744.0, 'LLDC': 3243.0}

        expected_output_package_4 = {'NIN': 0.0, 'TAD': 0.733906, 'CLC': 0.0573787, 'TNS': 311.0, 'TNM': 3391.0,
                                     'TNPM': 2772.0, 'TNG': 474.0, 'NCL': 0.0, 'TLOC': 64937.0, 'TNCL': 468.0,
                                     'TNDI': 83.0, 'TLLOC': 32802.0, 'PDA': 0.0, 'NPM': 0.0, 'TNPEN': 0.0, 'NG': 0.0,
                                     'TNPA': 185.0, 'NS': 0.0, 'LLOC': 0.0, 'NM': 0.0, 'CLOC': 0.0, 'LOC': 0.0,
                                     'TCD': 0.417454, 'CCL': 136.0, 'TNOS': 15663.0, 'TNPKG': 29.0, 'PUA': 0.0,
                                     'CI': 377.0, 'CC': 0.104568, 'LDC': 3726.0, 'AD': 0.0, 'TNIN': 23.0, 'TNEN': 0.0,
                                     'NA': 0.0, 'NPKG': 1.0, 'TNPCL': 305.0, 'NPA': 0.0, 'TCLOC': 23506.0, 'NEN': 0.0,
                                     'CD': 0.0, 'TNA': 1370.0, 'TNPIN': 20.0, 'CLLC': 0.0994694, 'CCO': 660.0,
                                     'TPDA': 2052.0, 'TNFI': 326.0, 'TPUA': 744.0, 'LLDC': 3243.0}

        expected_output_package_5 = {'NIN': 1.0, 'TAD': 0.733906, 'CLC': 0.0, 'TNS': 311.0, 'TNM': 3391.0,
                                     'TNPM': 2772.0, 'TNG': 474.0, 'NCL': 100.0, 'TLOC': 64937.0, 'TNCL': 468.0,
                                     'TNDI': 83.0, 'TLLOC': 32802.0, 'PDA': 975.0, 'NPM': 1116.0, 'TNPEN': 0.0,
                                     'NG': 120.0, 'TNPA': 185.0, 'NS': 81.0, 'LLOC': 10822.0, 'NM': 1260.0,
                                     'CLOC': 9264.0, 'LOC': 22601.0, 'TCD': 0.417454, 'CCL': 136.0, 'TNOS': 15663.0,
                                     'TNPKG': 28.0, 'PUA': 156.0, 'CI': 377.0, 'CC': 0.104568, 'LDC': 0.0,
                                     'AD': 0.862069, 'TNIN': 23.0, 'TNEN': 0.0, 'NA': 336.0, 'NPKG': 19.0,
                                     'TNPCL': 305.0, 'NPA': 46.0, 'TCLOC': 23506.0, 'NEN': 0.0, 'CD': 0.461217,
                                     'TNA': 1370.0, 'TNPIN': 20.0, 'CLLC': 0.0, 'CCO': 660.0, 'TPDA': 2052.0,
                                     'TNFI': 326.0, 'TPUA': 744.0, 'LLDC': 0.0}




        output = []
        with open(self.package_csv) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                output.append(parser.sanitize_metrics_dictionary(row))

        self.assertEqual(output[0], expected_output_package_1)
        self.assertEqual(output[1], expected_output_package_2)
        self.assertEqual(output[2], expected_output_package_3)
        self.assertEqual(output[3], expected_output_package_4)
        self.assertEqual(output[4], expected_output_package_5)



    def test_prepare_csv_files(self):
        parser = SourcemeterParser(self.out_java, self.input_path_java, "http://test.de", "2342", 'DEBUG')
        parser.prepare_csv_files()

        #test for correct sorting
        # lof4j.lsi
        entry = parser.ordered_file_states[0]
        self.assertEqual(entry['sortKey'], '0')
        self.assertEqual(entry['type'], 'component')
        self.assertEqual(entry['ID'], 'L103')
        self.assertNotIn('Parent', entry)

        # <System>
        entry = parser.ordered_file_states[1]
        self.assertEqual(entry['sortKey'], '0')
        self.assertEqual(entry['type'], 'component')
        self.assertEqual(entry['ID'], 'L102')
        self.assertNotIn('Parent', entry)

        # <root_package>
        entry = parser.ordered_file_states[2]
        self.assertEqual(entry['sortKey'], '1')
        self.assertEqual(entry['type'], 'package')
        self.assertEqual(entry['ID'], 'L100')
        self.assertEqual(entry['Parent'], '__LogicalRoot__')

        # unnamed_package
        entry = parser.ordered_file_states[3]
        self.assertEqual(entry['sortKey'], '100')
        self.assertEqual(entry['type'], 'package')
        self.assertEqual(entry['ID'], 'L104')
        self.assertEqual(entry['Parent'], 'L100')


        # org package
        entry = parser.ordered_file_states[4]
        self.assertEqual(entry['sortKey'], '100')
        self.assertEqual(entry['type'], 'package')
        self.assertEqual(entry['ID'], 'L649')
        self.assertEqual(entry['Parent'], 'L100')


        # AppenderTable.java
        entry = parser.ordered_file_states[5]
        self.assertEqual(entry['sortKey'], '104')
        self.assertEqual(entry['type'], 'class')
        self.assertEqual(entry['ID'], 'L124')
        self.assertEqual(entry['Parent'], 'L104')


        # org.apache package
        entry = parser.ordered_file_states[6]
        self.assertEqual(entry['sortKey'], '649')
        self.assertEqual(entry['type'], 'package')
        self.assertEqual(entry['ID'], 'L650')
        self.assertEqual(entry['Parent'], 'L649')


        # org.apache.log4j package
        entry = parser.ordered_file_states[7]
        self.assertEqual(entry['sortKey'], '650')
        self.assertEqual(entry['type'], 'package')
        self.assertEqual(entry['ID'], 'L651')
        self.assertEqual(entry['Parent'], 'L650')

        # TempFileAppender class
        entry = parser.ordered_file_states[8]
        self.assertEqual(entry['sortKey'], '651')
        self.assertEqual(entry['type'], 'class')
        self.assertEqual(entry['ID'], 'L6588')
        self.assertEqual(entry['Parent'], 'L651')

        # AsyncAppender class
        entry = parser.ordered_file_states[9]
        self.assertEqual(entry['sortKey'], '651')
        self.assertEqual(entry['type'], 'class')
        self.assertEqual(entry['ID'], 'L5123')
        self.assertEqual(entry['Parent'], 'L651')

    '''
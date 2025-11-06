"""
Unit tests for the FileClassifier module.
"""

from datetime import datetime
import pytest

from reorg_tool.classifier import FileClassifier
from reorg_tool.models import FileInfo, FileCategory


class TestFileClassifier:
    """Test cases for FileClassifier class."""
    
    @pytest.fixture
    def classifier(self):
        """Create a FileClassifier instance."""
        return FileClassifier()
    
    @pytest.fixture
    def sample_files(self):
        """Create sample file information for testing."""
        return [
            FileInfo(
                path="api/app.py",
                name="app.py",
                size=1024,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="models/predictor.py",
                name="predictor.py",
                size=2048,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="models/enhanced_predictor.py",
                name="enhanced_predictor.py",
                size=3072,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="data/processed/hiv_data_processed.csv",
                name="hiv_data_processed.csv",
                size=10240,
                extension=".csv",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="requirements.txt",
                name="requirements.txt",
                size=512,
                extension=".txt",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="README.md",
                name="README.md",
                size=2048,
                extension=".md",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="DEPLOYMENT_GUIDE.md",
                name="DEPLOYMENT_GUIDE.md",
                size=1536,
                extension=".md",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="docs/AI_INNOVATION.md",
                name="AI_INNOVATION.md",
                size=2560,
                extension=".md",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="PROJECT_STATUS.md",
                name="PROJECT_STATUS.md",
                size=1024,
                extension=".md",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="test_api.py",
                name="test_api.py",
                size=1024,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="evaluate_model.py",
                name="evaluate_model.py",
                size=2048,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="utils/data_generator.py",
                name="data_generator.py",
                size=1536,
                extension=".py",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="fix_bug.py",
                name="fix_bug.py",
                size=512,
                extension=".py",
                modified_time=datetime.now()
            ),
        ]
    
    def test_classifier_initialization(self, classifier):
        """Test FileClassifier initialization."""
        assert classifier is not None
        assert len(classifier.classification_rules) > 0
    
    def test_classify_core_api_file(self, classifier):
        """Test classification of core API files."""
        file_info = FileInfo(
            path="api/app.py",
            name="app.py",
            size=1024,
            extension=".py",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.CORE_API
    
    def test_classify_core_model_file(self, classifier):
        """Test classification of core model files."""
        file_info = FileInfo(
            path="models/predictor.py",
            name="predictor.py",
            size=2048,
            extension=".py",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.CORE_MODEL
    
    def test_classify_core_data_file(self, classifier):
        """Test classification of core data files."""
        file_info = FileInfo(
            path="data/processed/hiv_data_processed.csv",
            name="hiv_data_processed.csv",
            size=10240,
            extension=".csv",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.CORE_DATA
    
    def test_classify_config_file(self, classifier):
        """Test classification of configuration files."""
        file_info = FileInfo(
            path="requirements.txt",
            name="requirements.txt",
            size=512,
            extension=".txt",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.CONFIG
    
    def test_classify_user_doc_file(self, classifier):
        """Test classification of user documentation files."""
        file_info = FileInfo(
            path="README.md",
            name="README.md",
            size=2048,
            extension=".md",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.DOC_USER
    
    def test_classify_deployment_doc_file(self, classifier):
        """Test classification of deployment documentation files."""
        file_info = FileInfo(
            path="DEPLOYMENT_GUIDE.md",
            name="DEPLOYMENT_GUIDE.md",
            size=1536,
            extension=".md",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.DOC_DEPLOYMENT
    
    def test_classify_technical_doc_file(self, classifier):
        """Test classification of technical documentation files."""
        file_info = FileInfo(
            path="docs/AI_INNOVATION.md",
            name="AI_INNOVATION.md",
            size=2560,
            extension=".md",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.DOC_TECHNICAL
    
    def test_classify_project_doc_file(self, classifier):
        """Test classification of project documentation files."""
        file_info = FileInfo(
            path="PROJECT_STATUS.md",
            name="PROJECT_STATUS.md",
            size=1024,
            extension=".md",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.DOC_PROJECT
    
    def test_classify_test_file(self, classifier):
        """Test classification of test files."""
        file_info = FileInfo(
            path="test_api.py",
            name="test_api.py",
            size=1024,
            extension=".py",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.DEV_TEST
    
    def test_classify_dev_script_file(self, classifier):
        """Test classification of development script files."""
        file_info = FileInfo(
            path="evaluate_model.py",
            name="evaluate_model.py",
            size=2048,
            extension=".py",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.DEV_SCRIPT
    
    def test_classify_util_file(self, classifier):
        """Test classification of utility files."""
        file_info = FileInfo(
            path="utils/data_generator.py",
            name="data_generator.py",
            size=1536,
            extension=".py",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.DEV_UTIL
    
    def test_classify_temp_file(self, classifier):
        """Test classification of temporary files."""
        file_info = FileInfo(
            path="fix_bug.py",
            name="fix_bug.py",
            size=512,
            extension=".py",
            modified_time=datetime.now()
        )
        
        category = classifier.classify_file(file_info)
        assert category == FileCategory.DEV_TEMP
    
    def test_classify_batch(self, classifier, sample_files):
        """Test batch classification of files."""
        classified = classifier.classify_batch(sample_files)
        
        # Check that we have multiple categories
        assert len(classified) > 1
        
        # Check specific categories exist
        assert FileCategory.CORE_API in classified
        assert FileCategory.CORE_MODEL in classified
        assert FileCategory.CONFIG in classified
        assert FileCategory.DOC_USER in classified
    
    def test_detect_duplicates(self, classifier):
        """Test duplicate file detection."""
        files = [
            FileInfo(
                path="QUICK_START.md",
                name="QUICK_START.md",
                size=1024,
                extension=".md",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="QUICKSTART.md",
                name="QUICKSTART.md",
                size=1024,
                extension=".md",
                modified_time=datetime.now()
            ),
            FileInfo(
                path="QUICK_START_ENHANCED.md",
                name="QUICK_START_ENHANCED.md",
                size=1536,
                extension=".md",
                modified_time=datetime.now()
            ),
        ]
        
        duplicates = classifier.detect_duplicates(files)
        
        # Should detect similar files
        assert len(duplicates) > 0
        assert len(duplicates[0]['files']) >= 2
    
    def test_get_category_mapping(self, classifier):
        """Test category to directory mapping."""
        assert classifier.get_category_mapping(FileCategory.CORE_API) == 'core/api'
        assert classifier.get_category_mapping(FileCategory.CORE_MODEL) == 'core/models'
        assert classifier.get_category_mapping(FileCategory.CONFIG) == 'config'
        assert classifier.get_category_mapping(FileCategory.DOC_USER) == 'docs/user'
        assert classifier.get_category_mapping(FileCategory.DEV_TEST) == 'dev/tests'
    
    def test_generate_classification_report(self, classifier, sample_files):
        """Test classification report generation."""
        classified = classifier.classify_batch(sample_files)
        report = classifier.generate_classification_report(classified)
        
        assert "File Classification Report" in report
        assert "Total files:" in report
        assert len(report) > 100  # Should be a substantial report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

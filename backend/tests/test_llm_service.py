import pytest
from app.core import llm_service
from app.config import settings

@pytest.mark.asyncio
async def test_generate_text_fallback(mocker):
    # Ensure both keys are present so fallback logic triggers
    mocker.patch.object(settings, 'groq_api_key', 'test-groq-key')
    mocker.patch.object(settings, 'gemini_api_key', 'test-gemini-key')
    
    # Mock groq to raise an exception
    mock_groq = mocker.patch('app.core.llm_service._generate_text_groq', side_effect=Exception("Groq failure"))
    
    # Mock gemini to return a fallback response
    mock_gemini = mocker.patch('app.core.llm_service._generate_text_gemini', return_value="Gemini response")
    
    result = await llm_service.generate_text("Hello", "System")
    
    assert result == "Gemini response"
    mock_groq.assert_called_once_with("Hello", "System")
    mock_gemini.assert_called_once_with("Hello", "System")

@pytest.mark.asyncio
async def test_generate_text_groq_success(mocker):
    mocker.patch.object(settings, 'groq_api_key', 'test-groq-key')
    mocker.patch.object(settings, 'gemini_api_key', 'test-gemini-key')
    
    mock_groq = mocker.patch('app.core.llm_service._generate_text_groq', return_value="Groq response")
    mock_gemini = mocker.patch('app.core.llm_service._generate_text_gemini')
    
    result = await llm_service.generate_text("Hello", "System")
    
    assert result == "Groq response"
    mock_groq.assert_called_once_with("Hello", "System")
    mock_gemini.assert_not_called()

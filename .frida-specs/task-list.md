```xml
<tasks>
  <task>
    <task_name>Project Foundation and Setup</task_name>
    <subtasks>
      <subtask>
        <id>1</id>
        <name>Initialize project structure and dependencies</name>
        <description>Create the project directory structure, set up a Python virtual environment, and install required dependencies for document processing (PDF/image handling, OCR, vision-language models). Include libraries for multimodal AI inference, image processing, and JSON output handling.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>2</id>
        <name>Design module architecture and data structures</name>
        <description>Define the core architecture including input/output interfaces, document processing pipeline stages, and data structures for classification results and extracted fields. Plan how the module will orchestrate document reading, classification, and field extraction.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>3</id>
        <name>Create documentation and compliance notes</name>
        <description>Write README.md with clear warnings that this is a DEMO with fictional data only and must not be used with real patient data without proper security and compliance review. Include setup instructions and usage examples.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Document Input and Preprocessing</task_name>
    <subtasks>
      <subtask>
        <id>4</id>
        <name>Implement multimodal document reading</name>
        <description>Build functionality to accept and read both PDF and image files (jpg, png). Extract raw content using OCR for scanned documents and vision-language models for understanding document structure, layouts, and handwritten/printed text. Handle quality detection to identify low-quality or illegible content.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>5</id>
        <name>Add input validation and preprocessing</name>
        <description>Validate file types and sizes, normalize image orientation and resolution, handle edge cases like blank pages or corrupted files. Log warnings for quality issues that will affect confidence scores.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Document Classification System</task_name>
    <subtasks>
      <subtask>
        <id>6</id>
        <name>Implement document type classification</name>
        <description>Build a classification module that analyzes document content and structure to identify whether it belongs to: formulario_diabetes, laboratorio, estudio_diagnostico, or prescripcion. Use vision-language model capabilities to understand document semantics and layout patterns. Return both the classified type and a confidence score (0-100).</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>7</id>
        <name>Add classification confidence scoring</name>
        <description>Implement logic to calculate and assign classification confidence scores based on the clarity of document type indicators, presence of identifying headers/titles, and consistency of content with the classified category. Lower confidence when document is ambiguous or poor quality.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Field Extraction and Confidence Scoring</task_name>
    <subtasks>
      <subtask>
        <id>8</id>
        <name>Implement per-field extraction with individual confidence</name>
        <description>Build extraction logic that identifies and extracts the specific fields relevant to each document type (formulario_diabetes fields, laboratorio fields, prescripcion fields, estudio_diagnostico fields). Crucially, assign individual confidence scores (0-100) to each extracted field based on text clarity, field completeness, and data validity. Do not invent values for illegible or missing fields.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>9</id>
        <name>Implement quality and legibility handling</name>
        <description>Add logic to detect when content is illegible, unclear, or partially obscured. When extraction is uncertain, assign lower confidence scores rather than guessing values. Implement explicit handling for missing required fields vs. optional fields.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Inconsistency Detection and Validation</task_name>
    <subtasks>
      <subtask>
        <id>10</id>
        <name>Implement document completeness checking</name>
        <description>Build validation logic to detect and list missing required fields and critical inconsistencies specific to each document type. Examples include: missing physician signature on formulario_diabetes, missing study date on laboratorio, expired prescription dates on prescripcion, etc.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>11</id>
        <name>Add data consistency and logic validation</name>
        <description>Implement checks for logical inconsistencies (e.g., study date in the future, conflicting diagnosis dates, medication dosages outside normal ranges). Flag these explicitly in the output without attempting to correct them.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Output Formatting and JSON Response</task_name>
    <subtasks>
      <subtask>
        <id>12</id>
        <name>Implement JSON output schema</name>
        <description>Build the output formatting layer that generates JSON responses following the exact specified structure: tipo_documento, confianza_clasificacion, campos_extraidos (with value and per-field confidence), and faltantes_o_inconsistencias list. Ensure all JSON is properly formatted and validated.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>13</id>
        <name>Add logging and error handling</name>
        <description>Implement comprehensive error handling for processing failures, invalid inputs, and edge cases. Provide meaningful error messages. Add optional logging for debugging that can be toggled for production/demo use.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Testing with Fictional Documents</task_name>
    <subtasks>
      <subtask>
        <id>14</id>
        <name>Create fictional test documents</name>
        <description>Generate or create at least one realistic fictional test document for each document type: a formulario_diabetes (signed, with doctor data), a laboratorio (with test results), a prescripcion (with medication and dosage), and an estudio_diagnostico (diagnostic report). Use realistic but clearly fictional patient/doctor names and data. Include some documents with quality issues or missing fields for comprehensive testing.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>15</id>
        <name>Implement and execute integration tests</name>
        <description>Build a test script that processes each fictional document through the complete pipeline and validates that the output matches expected results. Test edge cases including low-quality images, missing fields, unclear text, and mixed document types. Document expected outputs for each test case.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>16</id>
        <name>Create usage examples and documentation</name>
        <description>Write clear examples showing how to use the module with each document type, including sample code snippets and expected output JSON. Provide a demo script that processes test documents and displays formatted results. Include explanations of confidence scores and how to interpret the output.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Verification and Deliverables</task_name>
    <subtasks>
      <subtask>
        <id>17</id>
        <name>Verify module functionality against requirements</name>
        <description>Conduct final verification that the module meets all specified requirements: accepts PDF and images, performs multimodal reading, classifies documents correctly, extracts required fields with individual confidence scores, detects inconsistencies, and produces correct JSON output format. Ensure no hardcoded example values are present.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>18</id>
        <name>Prepare final deliverables</name>
        <description>Organize all code, documentation, test documents, and examples into a complete, ready-to-use module package. Verify that README clearly states this is a DEMO with fictional data only. Include instructions for setup, usage, and testing. Ensure the module is self-contained and functional.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Web Interface for Document Upload and JSON Display</task_name>
    <subtasks>
      <subtask>
        <id>19</id>
        <name>Design and build simple web interface</name>
        <description>Create a clean, user-friendly web interface using HTML/CSS with a file upload section that accepts documents (PDF and image files). Design the UI with two main sections: an upload area at the top with a file selector button, and a results area below where the JSON output will be displayed.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>20</id>
        <name>Implement client-side file handling and validation</name>
        <description>Add JavaScript functionality to handle file selection, validate file types (PDF, JPG, PNG) and sizes before submission. Provide user feedback for invalid files. Display file name and status of selected file.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>21</id>
        <name>Create backend API endpoint for document processing</name>
        <description>Build a REST API endpoint that receives uploaded documents, processes them through the existing document processing module, and returns the JSON result with document classification, extracted fields with confidence scores, and validation results.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>22</id>
        <name>Implement JSON display and formatting in web interface</name>
        <description>Add JavaScript to receive the JSON response from the backend and display it in a formatted, readable way below the upload section. Use syntax highlighting or structured display for clarity. Include error handling to show meaningful messages if processing fails.</description>
        <completed>true</completed>
      </subtask>
      <subtask>
        <id>23</id>
        <name>Add loading states and user experience enhancements</name>
        <description>Implement loading indicators while documents are being processed, disable upload button during processing, show success/error messages, and allow users to upload multiple documents sequentially. Add a clear button to reset the interface for new uploads.</description>
        <completed>true</completed>
      </subtask>
    </subtasks>
  </task>

  <task>
    <task_name>Debug and Fix Field Extraction Issues</task_name>
    <subtasks>
      <subtask>
        <id>24</id>
        <name>Analyze laboratorio_sample.png to identify actual field locations and content</name>
        <description>Load and visually examine the laboratorio_sample.png file to understand the document layout and identify where laboratorio_nombre and medico_solicitante fields are actually positioned and what text/values they contain. Use the vision-language model to extract raw text from these specific regions and analyze why the current extraction is failing to detect them.</description>
        <completed>false</completed>
      </subtask>
      <subtask>
        <id>25</id>
        <name>Update field detection patterns and extraction logic for laboratorio documents</name>
        <description>Refine the field extraction logic specifically for laboratorio documents to properly locate and extract laboratorio_nombre and medico_solicitante fields. Improve text recognition accuracy for these fields, enhance pattern matching to account for different formatting styles, and ensure the extraction assigns appropriate confidence scores based on actual text clarity rather than defaulting to NOT_FOUND when the fields are present in the document.</description>
        <completed>false</completed>
      </subtask>
      <subtask>
        <id>26</id>
        <name>Verify corrected extraction on laboratorio_sample.png and test</name>
        <description>Re-process laboratorio_sample.png with the updated extraction logic and verify that laboratorio_nombre and medico_solicitante are now correctly identified and extracted with appropriate confidence scores. Document the actual extracted values, compare them against what is visually present in the image, and confirm the fix resolves the NOT_FOUND issues.</description>
        <completed>false</completed>
      </subtask>
    </subtasks>
  </task>
</tasks>
```
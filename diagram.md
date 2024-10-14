::: mermaid
flowchart LR
  subgraph repo [Codebase Repository]
    direction LR
    subgraph helpers_group [helpers.py]
      helpers_generate_unique_filename["generate_unique_filename"]
      helpers_save_content_to_file["save_content_to_file"]
      helpers_is_irrelevant_file["is_irrelevant_file"]
    end
    
    subgraph config_group [config.py]
      config_constants["Constants"]
      config_llm_urls["LLM URLs"]
      config_output_dirs["Output Directories"]
    end
    
    subgraph codeconcat_group [codeconcat.py]
      codeconcat_combine_python_files["combine_python_files"]
    end
    
    subgraph llm_interface_group [llm_interface.py]
      llm_read_files["File Reading"]
      llm_generate_summary["Generate Summary"]
      llm_cache_results["Cache Summaries"]
    end
    
    subgraph main_group [main.py]
      main_logging["Logging"]
      main_summarize_codebase["Summarize Codebase"]
      main_generate_diagram_prompt["Generate Diagram Prompt"]
      main_output_handler["Handle Outputs"]
    end
    
    subgraph file_readers [File Readers]
      text_reader["text_reader"]
      pptx_reader["pptx_reader"]
      docx_reader["docx_reader"]
      pdf_reader["pdf_reader"]
      html_reader["html_reader"]
    end
    
    subgraph diagram_generators [Diagram Generators]
      plantuml_generator["plantuml_generator"]
      mermaid_generator["mermaid_generator"]
    end
  end

  llm_interface_group -->|Uses Config| config_group
  main_group -->|Uses File Readers| file_readers
  main_group -->|Calls Summarization| llm_interface_group
  llm_interface_group -->|Summarizes Files| text_reader
  llm_interface_group -->|Summarizes Files| pptx_reader
  llm_interface_group -->|Summarizes Files| docx_reader
  llm_interface_group -->|Summarizes Files| pdf_reader
  llm_interface_group -->|Summarizes Files| html_reader
  main_group -->|Generates Diagram| diagram_generators
  diagram_generators -->|Uses Summaries| llm_interface_group
  helpers_group -->|Assists with File Handling| main_group
  codeconcat_group -->|Combines Files| main_group

:::
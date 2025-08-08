import os
import tempfile
from typing import Dict, Any, Optional
import graphviz
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

class ClassDiagramGenerator:
    """Generates class diagrams using OpenAI and Graphviz."""
    
    def __init__(self):
        self.openai_client = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    async def generate_diagram(self, repository_info: Dict[str, Any]) -> Optional[str]:
        """Generate a class diagram for a repository."""
        try:
            # Extract relevant code structure using OpenAI
            dot_code = await self._extract_class_structure(repository_info)
            
            if not dot_code:
                return None
            
            # Generate the diagram
            diagram_path = self._create_diagram(dot_code)
            return diagram_path
            
        except Exception as e:
            print(f"Error generating class diagram: {e}")
            return None
    
    async def _extract_class_structure(self, repo_info: Dict[str, Any]) -> str:
        """Use OpenAI to analyze repository and generate DOT notation."""
        system_prompt = """You are a software architect. Create a class diagram in valid DOT notation.

        Rules:
        - Use only valid DOT syntax
        - Use double quotes for labels, never backticks
        - Keep class names simple (no special characters)
        - Focus on main classes and relationships
        - Use -> for relationships
        - Example format:
        
        digraph ClassDiagram {
            rankdir=TB;
            node [shape=record];
            
            ClassA [label="ClassA|+method1()|+method2()"];
            ClassB [label="ClassB|+method3()"];
            ClassA -> ClassB;
        }
        
        Return ONLY valid DOT code, no explanations or markdown."""
        
        user_prompt = f"""Repository: {repo_info.get('name', 'Unknown')}
        Description: {repo_info.get('description', 'No description')}
        Language: {repo_info.get('language', 'Unknown')}
        
        Create a class diagram in DOT notation for this repository's likely architecture."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.openai_client.ainvoke(messages)
        return response.content.strip()
    
    def _create_diagram(self, dot_code: str) -> str:
        """Create diagram file from DOT code."""
        # Clean DOT code - remove markdown formatting and fix syntax
        dot_code = dot_code.strip()
        
        # Remove markdown code blocks
        if dot_code.startswith('```'):
            lines = dot_code.split('\n')
            dot_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else dot_code
        
        # Remove backticks and other problematic characters
        dot_code = dot_code.replace('`', '"').replace(''', '"').replace(''', '"')
        
        # Ensure proper DOT structure
        if not dot_code.startswith('digraph') and not dot_code.startswith('graph'):
            dot_code = f"digraph ClassDiagram {{\n{dot_code}\n}}"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_code)
            dot_file = f.name
        
        try:
            # Generate PNG
            graph = graphviz.Source.from_file(dot_file)
            output_path = dot_file.replace('.dot', '.png')
            graph.render(output_path.replace('.png', ''), format='png', cleanup=True)
            
            # Clean up dot file
            os.unlink(dot_file)
            
            return output_path
            
        except Exception as e:
            print(f"Error creating diagram: {e}")
            if os.path.exists(dot_file):
                os.unlink(dot_file)
            return None

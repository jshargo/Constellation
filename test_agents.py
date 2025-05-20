import agents
import inspect

# Print out the Tool class to understand its structure
print("Tool class:", agents.Tool)
print("Tool module:", inspect.getmodule(agents.Tool))

# Try to create a simple tool
def simple_function(x: int) -> str:
    """A simple function that returns a string."""
    return f"You provided {x}"

try:
    # Try different ways to create a tool
    print("\nAttempting to create a tool...")
    
    # Method 1: Using function directly
    print("\nMethod 1:")
    tool1 = agents.tool(simple_function)
    print(f"Tool 1: {tool1}")
    
    # Method 2: Using decorator
    print("\nMethod 2:")
    @agents.tool
    def decorated_function(x: int) -> str:
        """A decorated function."""
        return f"Decorated: {x}"
    
    print(f"Decorated function: {decorated_function}")
    
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")

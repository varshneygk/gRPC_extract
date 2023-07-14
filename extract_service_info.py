import argparse
import importlib.util
import json
import os
from google.protobuf.descriptor import FieldDescriptor
from collections import defaultdict

python_type_mapping = {
    1: "double",
    2: "float",
    3: "int64",
    4: "uint64",
    5: "int32",
    6: "fixed64",
    7: "fixed32",
    8: "bool",
    9: "string",
    10: "group",
    11: "message",
    12: "bytes",
    13: "uint32",
    14: "enum",
    15: "sfixed32",
    16: "sfixed64",
    17: "sint32",
    18: "sint64"
}

python_type_mapping = defaultdict(lambda: None, python_type_mapping)

cpp_type_mapping = {
    1: "int32",
    2: "int64",
    3: "uint32",
    4: "uint64",
    5: "double",
    6: "float",
    7: "bool",
    8: "enum",
    9: "string",
    10: "message"
}

cpp_type_mapping = defaultdict(lambda: None, cpp_type_mapping)

label_mapping = {
    1: "optional",
    2: "required",
    3: "repeated"
}

label_mapping = defaultdict(lambda: None, label_mapping)

def extract_field_info(field):
    
    field_info = {
        "name": field.name,
        "type": python_type_mapping[field.type],
        "cpp_type": cpp_type_mapping[field.cpp_type],
        "default_value": field.default_value,
        "label": label_mapping[field.label],
        "is_optional": field.label == FieldDescriptor.LABEL_OPTIONAL,
        "is_repeated": field.label == FieldDescriptor.LABEL_REPEATED
    }

    if field.message_type:
        field_info["data_type"] = field.message_type.full_name
    elif field.enum_type:
        field_info["data_type"] = field.enum_type.full_name
    else:
        field_info["data_type"] = field.type

    if field.has_default_value:
        field_info["default_value"] = field.default_value

    return field_info

def extract_service_information(proto_module, proto_file):
    service_info_list = []

    # Iterate over all services in the module
    for service_name, service_descriptor in proto_module.DESCRIPTOR.services_by_name.items():
        # Extract service information
        service_name = service_descriptor.full_name
        service_methods = []

        # Extract information for each service method
        for method in service_descriptor.methods:
            method_name = method.name
            input_type = method.input_type.full_name
            output_type = method.output_type.full_name

            # Get the message descriptors for the input and output types
            input_message = proto_module.DESCRIPTOR.message_types_by_name[input_type]
            output_message = proto_module.DESCRIPTOR.message_types_by_name[output_type]

            # Extract information about the input message fields
            input_fields = [extract_field_info(field) for field in input_message.fields]

            # Extract information about the output message fields
            output_fields = [extract_field_info(field) for field in output_message.fields]

            # Create a dictionary for the method information
            method_info = {
                "name": method_name,
                "input_type": input_type,
                "output_type": output_type,
                "input_fields": input_fields,
                "output_fields": output_fields
            }

            # Add the method information to the list
            service_methods.append(method_info)

        # Create a dictionary for the service information
        service_info = {
            "name": service_name,
            "methods": service_methods
        }

        service_info_list.append(service_info)

    return service_info_list

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("directory_path", help="Path to the directory containing the .proto and _pb2.py files")
parser.add_argument("output_file", help="Output file path for the service information JSON")
args = parser.parse_args()

# Locate the .proto and _pb2.py files in the directory
proto_file = None
proto_module_path = None

for file_name in os.listdir(args.directory_path):
    if file_name.endswith(".proto"):
        proto_file = os.path.join(args.directory_path, file_name)
    elif file_name.endswith("_pb2.py"):
        proto_module_path = os.path.join(args.directory_path, file_name)

# Load the proto module dynamically
spec = importlib.util.spec_from_file_location("proto_module", proto_module_path)
proto_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proto_module)

# Extract service information
service_info_list = extract_service_information(proto_module, proto_file)

# Write the service information as JSON to the output file
with open(args.output_file, "w") as f:
    json.dump(service_info_list, f, indent=2)

print("Service information has been written to", args.output_file)

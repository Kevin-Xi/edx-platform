def yield_dynamic_descriptor_descendents(descriptor, module_creator):
    """
    This returns all of the descendants of a descriptor. If the descriptor
    has dynamic children, the module will be created using module_creator
    and the children (as descriptors) of that module will be returned.
    """
    def get_dynamic_descriptor_children(descriptor):
        if descriptor.has_dynamic_children():
            module = module_creator(descriptor)
            if module is None:
                return []
            return module.get_child_descriptors()
        else:
            return descriptor.get_children()

    stack = [descriptor]

    while len(stack) > 0:
        next_descriptor = stack.pop()
        stack.extend(get_dynamic_descriptor_children(next_descriptor))
        yield next_descriptor

## Span Attribute Types

Span attributes can be added in two ways.

`--span-attributes key=value` assumes `value` is of type `string`.

For example, `--span-attributes foo=bar`

Alternatively, you can explicitely specify the `value` type:
`--span-attributes key=value`.

For example, `--span-attributes userID=123=intValue`


The short form `--spnattrs foo=bar` is also valid.

### Valid Types

The following are all valid:

- `stringValue`
- `boolValue`
- `intValue`
- `doubleValue`
- `arrayValue`
- `kvlistValue`
- `bytesValue`
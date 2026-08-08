# Central lookup catalog QA Report

Execution timestamp: 20260725T045827Z
Runtime: Python 3.13.7; openpyxl 3.1.5
ZIP integrity/openpyxl load: PASS for selected and output XLSX artifacts.
Excel COM status: Not executed; non-blocking.
Source-hash preservation: PASS
QA status: PASS WITH WARNINGS

```json
{
  "execution_id": "NX-LKUP-20260725T045827Z",
  "runtime": "Python 3.13.7; openpyxl 3.1.5",
  "manifest": "D:\\Business Portal\\100_Master_Data\\Governance\\Lookup Governance\\Reviewed Baseline\\Nocturnix_Lookup_Governance_Baseline_Manifest_20260725T045827Z.csv",
  "decision_summary": [
    {
      "CrosswalkDomain": "ManufacturerID",
      "ApprovedRows": 20,
      "TotalRows": 20
    },
    {
      "CrosswalkDomain": "DeviceFamilyID",
      "PendingRows": 1,
      "ApprovedRows": 126,
      "TotalRows": 127
    },
    {
      "CrosswalkDomain": "DeviceTypeID",
      "ApprovedRows": 12,
      "TotalRows": 12
    }
  ],
  "applied_mappings": {
    "DeviceFamilyID": 164
  },
  "duplicate_summary_count": 13,
  "registry_issue_count": 53,
  "data_dictionary_issue_count": 247,
  "source_hashes_before": {
    "ID crosswalk workbook": "abaf968d41b67550216646eeee406f02a7e74c7421759b2f04f73065afbaf5c0",
    "Model duplicate review workbook": "94be15bff203bc7fe6866ecc4ee4fd996196badd54d44c320bba13e1d9ae57a8",
    "Device working catalog": "d230b29e0034cc4652e37000390a66d56510d70fbdbb744d42e0e9326e3ce0da",
    "Central lookup catalog": "fa60c80e338474b1d41cab02b2fdd55122a68a008b37197e1e905951c9a9973f",
    "Lookup Registry": "f70dc676c8cf67ec2b36ae3dcb795ab9e18740feb3f00f12679adc6a576f2f15",
    "Data Dictionary": "579f0b67594aab3eadbac9438e19ae91af0af4827fc39d3afe8a0945a0a34eee",
    "Governance Change Log": "8670ed4963fbe02684103507ef3afe8fb51e1751d6ef568adadc27420d8685df",
    "Governance Standard": "ddf5d4ccad2d1eafed1561055a91da8ffbeb564cf9542bdcfa4ac12aea946646"
  },
  "source_hashes_after": {
    "ID crosswalk workbook": "abaf968d41b67550216646eeee406f02a7e74c7421759b2f04f73065afbaf5c0",
    "Model duplicate review workbook": "94be15bff203bc7fe6866ecc4ee4fd996196badd54d44c320bba13e1d9ae57a8",
    "Device working catalog": "d230b29e0034cc4652e37000390a66d56510d70fbdbb744d42e0e9326e3ce0da",
    "Central lookup catalog": "fa60c80e338474b1d41cab02b2fdd55122a68a008b37197e1e905951c9a9973f",
    "Lookup Registry": "f70dc676c8cf67ec2b36ae3dcb795ab9e18740feb3f00f12679adc6a576f2f15",
    "Data Dictionary": "579f0b67594aab3eadbac9438e19ae91af0af4827fc39d3afe8a0945a0a34eee",
    "Governance Change Log": "8670ed4963fbe02684103507ef3afe8fb51e1751d6ef568adadc27420d8685df",
    "Governance Standard": "ddf5d4ccad2d1eafed1561055a91da8ffbeb564cf9542bdcfa4ac12aea946646"
  },
  "output_hashes": {
    "Device catalog": "9d35b4821f6c1b0c6560ba00d01e0b8a1be5cf385b23ba3c5739b8880d15da9a",
    "Central lookup catalog": "c6455b72d061df1d47777dd5bc6b0081ce27cbb721770ab4d8497353efeb49de",
    "ID crosswalk workbook": "94169bb16a0ca26916db51226a836d409b5f672ae6a0dc9726bbf89f517740f3",
    "Lookup Registry": "b1614d26bcc427e4092182bf8d18fd0161c3d491e14cc94b4e6d8880e68af6e5",
    "Data Dictionary": "f962270092f45db0b522a5a4fa395be4ac6ec8952026fcae69130f897d7f8853",
    "Duplicate review": "577653df11b486b6409b796e47b93efa15fe3fdd324e15dc6cfae0bf782c6e38",
    "Change log": "2eaa7a4d3490d99fcee3b541ebbd6d5ff863993b99e542df491e5fca94e73aa0"
  },
  "qa_status": "PASS WITH WARNINGS",
  "readiness": [
    "NOT DATABASE-IMPORT READY",
    "NOT PRODUCTION READY"
  ]
}
```

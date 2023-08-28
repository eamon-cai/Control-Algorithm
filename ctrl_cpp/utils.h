#pragma once
#include <iostream>
#include <algorithm> // for std::min and std::max
#include <stdexcept> // for std::invalid_argument
#include <vector>
using std::vector;
using std::pair;

// �������ݷ�Χ
double clip(double x, double x_min, double x_max);
vector<double> clip(const vector<double>& x, const vector<double>& x_min, const vector<double>& x_max);
vector<double> clip(const vector<double>& x, double x_min, const vector<double>& x_max);
vector<double> clip(const vector<double>& x, const vector<double>& x_min, double x_max);
vector<double> clip(const vector<double>& x, double x_min, double x_max);

// ���ź���
double sign(double x);
int sign(int x);

// ��ӡ����
void printMatrix(const vector<vector<double>>& matrix);

// ����ת��
vector<vector<double>> matrixTranspose(const vector<vector<double>>& matrix);

// ����˷�
vector<vector<double>> matrixMultiply(const vector<vector<double>>& matrixA, const vector<vector<double>>& matrixB);
vector<double> matrixMultiply(const vector<vector<double>>& matrixA, const vector<double>& matrixB);

// ����ӷ�
vector<vector<double>> matrixAddition(const vector<vector<double>>& matrixA, const vector<vector<double>>& matrixB, bool sub = false);
vector<double> matrixAddition(const vector<double>& matrixA, const vector<double>& matrixB, bool sub = false);

// ��λ����
vector<vector<double>> matrixiIdentity(int n);

// ��������ʽ
double matrixDeterminant(const vector<vector<double>>& matrix);

// ��������
vector<vector<double>> matrixInverse(const vector<vector<double>>& matrix);

// ��������
vector<vector<double>> matrixPow(const vector<vector<double>>& matrix, int power);

// ��������
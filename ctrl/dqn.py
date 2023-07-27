# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 15:43:28 2022

@author: HJ
"""

''' DQN '''
# model based controller

import pylab as pl
from copy import deepcopy
from dataclasses import dataclass

if __name__ == '__main__':
    import sys, os
    ctrl_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ctrl包所在的目录
    sys.path.append(ctrl_dir)
    
from ctrl.common import BaseDRLController, SignalLike
from ctrl.demo import *

__all__ = ['DQNConfig', 'DQN']


# DQN控制器参数
@dataclass
class DQNConfig:
    """PID控制算法参数
    :param dt: float, 控制器步长
    :param dim: int, 输入信号维度, 即控制器输入v、y的维度, PID输出u也为dim维
    :param Kp: SignalLike, PID比例增益系数
    :param Ki: SignalLike, PID积分增益系数
    :param Kd: SignalLike, PID微分增益系数
    :param u_max: SignalLike, 控制律上限, 范围: (u_min, inf], 取inf时不设限
    :param u_min: SignalLike, 控制律下限, 范围: [-inf, u_max), 取-inf时不设限
    :param Kaw: SignalLike, 抗积分饱和参数, 最好取: 0.1~0.3, 取0时不抗饱和
    :param max_err: SignalLike, 积分器分离阈值, 范围: (0, inf], 取inf时不分离积分器
    :Type : SignalLike = float (标量) | list / ndarray (一维数组即向量)\n
    备注:\n
    dim>1时SignalLike为向量时, 相当于同时设计了dim个不同的PID控制器, 必须满足dim==len(SignalLike)\n
    dim>1时SignalLike为标量时, 相当于设计了dim个参数相同的PID控制器, 控制效果可能不好\n
    """
    dt: float = 0.001            # 控制器步长 (float)
    dim: int = 1                 # 输入维度 (int)
    # PID控制器增益
    Kp: SignalLike = 5           # 比例增益 (float or list)
    Ki: SignalLike = 0.001       # 积分增益 (float or list)
    Kd: SignalLike = 10          # 微分增益 (float or list)
    # 抗积分饱和
    u_max: SignalLike = pl.inf   # 控制律上限, 范围: (u_min, inf], 取inf时不设限 (float or list)
    u_min: SignalLike = -pl.inf  # 控制律下限, 范围: [-inf, u_max), 取-inf时不设限 (float or list)
    Kaw: SignalLike = 0.2        # 抗饱和参数, 最好取: 0.1~0.3, 取0时不抗饱和 (float or list)
    max_err: SignalLike = pl.inf # 积分器分离阈值, 范围: (0, inf], 取inf时不分离积分器 (float or list)



# DQN控制算法
class DQN(BaseDRLController):
    """DQN强化学习控制算法"""

    def __init__(self, cfg: DQNConfig):
        super().__init__()
        self.name = 'DQN'      # 算法名称
        self.dt = cfg.dt       # 控制器步长
        self.dim = cfg.dim     # 反馈信号y和跟踪信号v的维度
        
        # PID超参（不需要遍历的数据设置为一维数组）
        self.Kp = pl.array(cfg.Kp).flatten() # Kp array(dim,) or array(1,)
        self.Ki = pl.array(cfg.Ki).flatten() # Ki array(dim,) or array(1,)
        self.Kd = pl.array(cfg.Kd).flatten() # Kd array(dim,) or array(1,)
        self.Kaw = pl.array(cfg.Kaw).flatten() / self.Kd # Kaw取 0.1~0.3 Kd
        
        # 抗积分饱和PID（需要遍历的数据设置为一维数组，且维度保持和dim一致）
        self.u_max = pl.array(cfg.u_max).flatten() # array(1,) or array(dim,)
        self.u_max = self.u_max.repeat(self.dim) if len(self.u_max) == 1 else self.u_max # array(dim,)
        self.u_min = pl.array(cfg.u_min).flatten() # array(1,) or array(dim,)
        self.u_min = self.u_min.repeat(self.dim) if len(self.u_min) == 1 else self.u_min # array(dim,)
        self.max_err = pl.array(cfg.max_err).flatten() # array(1,) or array(dim,)
        self.max_err = self.max_err.repeat(self.dim) if len(self.max_err) == 1 else self.u_min # array(dim,)
        
        # 控制器初始化
        self.u = pl.zeros(self.dim)            # array(dim,)
        self.error_last = pl.zeros(self.dim)   # array(dim,)
        self.integration = pl.zeros(self.dim)  # array(dim,)
        self.t = 0
        
        # 存储器
        self.logger.e = []    # 误差
        self.logger.d = []    # 误差微分
        self.logger.i = []    # 误差积分
    
    # PID控制器（v为参考轨迹，y为实际轨迹或其观测值）
    def __call__(self, v, y) -> pl.ndarray:
        # 计算PID误差
        error = pl.array(v - y).flatten()              # P偏差 array(dim,)
        differential = error - self.error_last         # D偏差 array(dim,)
        
        # 抗积分饱和算法
        beta = self._anti_integral_windup(error, method=2) # 积分分离参数 array(dim,)
        
        # 控制量
        self.u = self.Kp * error + beta * self.Ki * self.integration + self.Kd * differential
        self.u = pl.clip(self.u, self.u_min, self.u_max)
        self.error_last = deepcopy(error)
        
        # 存储绘图数据
        self.logger.t.append(self.t)
        self.logger.u.append(self.u)
        self.logger.y.append(y)
        self.logger.v.append(v)
        self.logger.e.append(error)
        self.logger.d.append(differential)
        self.logger.i.append(self.integration)
        
        self.t += self.dt
        return self.u
    
    # 抗积分饱和算法 + 积分分离
    def _anti_integral_windup(self, error, method = 2):
        beta = pl.zeros(self.dim) # 积分分离参数
        gamma = pl.zeros(self.dim) if method < 2 else None # 方法1的抗积分饱和参数
        for i in range(self.dim):
            # 积分分离，误差超限去掉积分控制
            beta[i] = 0 if abs(error[i]) > self.max_err[i] else 1 
            
            # 算法1
            if method < 2:
                # 控制超上限累加负偏差，误差超限不累加
                if self.u[i] > self.u_max[i]:
                    if error[i] < 0:
                        gamma[i] = 1 # 负偏差累加
                    else:
                        gamma[i] = 0 # 正偏差不累加
                # 控制超下限累加正偏差，误差超限不累加
                elif self.u[i] < self.u_max[i]:
                    if error[i] > 0:
                        gamma[i] = 1 # 正偏差累加
                    else:
                        gamma[i] = 0 # 负偏差不累加
                else:
                    gamma[i] = 1 # 控制不超限，正常累加偏差
                #end if
            #end if
        #end for
                
        # 抗饱和算法1
        self.integration += error if method > 1 else beta * gamma * error # 正常积分PID
        # self.integration += error/2 if method > 1 else beta * gamma * error/2 # 梯形积分PID
        
        # 反馈抑制抗饱和算法 back-calculation
        if method > 1:
            antiWindupError = pl.clip(self.u, self.u_min, self.u_max) - self.u
            self.integration += self.Kaw * antiWindupError # 累计误差加上个控制偏差的反馈量
        
        return beta
            
    
    def show(self, *, save = False):
        # 响应曲线 与 控制曲线
        super().show(save=save)
        
        # 误差曲线
        self._figure(fig_name='Error Curve', t=self.logger.t,
                     y1=self.logger.e, y1_label='error',
                     xlabel='time', ylabel='error signal', save=save)
        self._figure(fig_name='Differential of Error Curve', t=self.logger.t,
                     y1=self.logger.d, y1_label='differential of error',
                     xlabel='time', ylabel='error differential signal', save=save)
        self._figure(fig_name='Integration of Error Curve', t=self.logger.t,
                     y1=self.logger.i, y1_label='integration of error',
                     xlabel='time', ylabel='error integration signal', save=save)
        
        # 显示图像
        pl.show()
        
        
        


'debug'
if __name__ == '__main__':
    pass
